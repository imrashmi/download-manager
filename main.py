import os
import requests
import time
import libtorrent as lt
import subprocess
from tqdm import tqdm
from urllib.parse import urlparse, unquote
from mega import Mega

# Function to automatically install missing dependencies
def install_dependencies():
    required_libs = ['python-libtorrent', 'requests', 'tqdm', 'mega.py']
    for lib in required_libs:
        try:
            subprocess.check_call(['pip', 'install', lib])
        except subprocess.CalledProcessError as e:
            print(f"Error installing {lib}: {e}")

# Install dependencies before proceeding
install_dependencies()

# Mega.nz login function (uses environment variables for simplicity)
def mega_login():
    mega = Mega()
    email = os.getenv("MEGA_EMAIL")
    password = os.getenv("MEGA_PASSWORD")
    if not email or not password:
        email = input("Enter your Mega.nz email: ")
        password = input("Enter your Mega.nz password: ")
    m = mega.login(email, password)
    return m

# Upload the file to Mega.nz with progress tracking
def upload_to_mega(file_path):
    m = mega_login()
    file_name = os.path.basename(file_path)

    # Upload file with progress bar
    with tqdm(total=os.path.getsize(file_path), unit='iB', unit_scale=True, desc=f"Uploading {file_name}") as progress_bar:
        file_response = m.upload(file_path)
        progress_bar.update(os.path.getsize(file_path))

    # Get the shareable link using the response from the upload method
    public_link = m.get_upload_link(file_response)
    print(f"\nUpload complete! Shareable link: {public_link}")
    return public_link

# Function to determine if the user wants torrent or direct download
def ask_for_download_type():
    while True:
        choice = input("Is this a torrent download? (y/n): ").lower()
        if choice in ['y', 'n']:
            return choice == 'y'
        else:
            print("Please choose 'y' or 'n'.")

# Function to ask for torrent type (magnet URI, .torrent file, or .torrent link)
def ask_for_torrent_type():
    while True:
        print("\nChoose Torrent Type:")
        print("1. Magnet URI")
        print("2. Upload a .torrent file")
        print("3. .torrent file download link")
        choice = input("Select (1/2/3): ")
        if choice in ['1', '2', '3']:
            return choice
        else:
            print("Invalid choice, please select 1, 2, or 3.")

# Function to extract file name from URL or magnet URI
def extract_filename_from_url_or_magnet(url_or_magnet):
    if url_or_magnet.startswith('magnet:?'):
        # Extract info hash from magnet URI
        return url_or_magnet.split('&')[0].split(':')[-1]  # Extract the torrent hash as the name
    else:
        parsed_url = urlparse(url_or_magnet)
        filename = os.path.basename(parsed_url.path)
        return unquote(filename)  # Decode URL-encoded characters

# Function to download a torrent via Magnet URI
def download_torrent_magnet(magnet_link):
    ses = lt.session()
    params = {
        'save_path': './',
        'storage_mode': lt.storage_mode_t(2),
    }
    handle = lt.add_magnet_uri(ses, magnet_link, params)

    print("Downloading metadata...")
    while not handle.has_metadata():
        time.sleep(1)
    
    info = handle.get_torrent_info()
    torrent_name = info.name()
    save_dir = os.path.join('.', torrent_name)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    print(f"Downloading torrent: {torrent_name}")
    handle = lt.add_torrent({'ti': info, 'save_path': save_dir})

    progress_bar = tqdm(total=info.total_size(), unit='iB', unit_scale=True, desc=torrent_name)
    while not handle.is_seed():
        status = handle.status()
        progress_bar.update(int(status.progress * info.total_size()) - progress_bar.n)
        progress_bar.set_postfix_str(f"Download Speed: {status.download_rate / 1024:.2f} kB/s")
        time.sleep(1)

    progress_bar.close()
    print(f"Torrent download complete: {torrent_name}")

    return save_dir  # Return the path of the downloaded torrent folder

# Function to download a .torrent file and proceed with the torrent download
def download_torrent_file(torrent_url_or_path, is_url=True):
    if is_url:
        # Download the .torrent file from the provided URL
        print("\nDownloading .torrent file from URL...\n")
        response = requests.get(torrent_url_or_path)
        filename = extract_filename_from_url_or_magnet(torrent_url_or_path)
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f".torrent file downloaded: {filename}")
    else:
        # Use the provided file directly
        filename = torrent_url_or_path

    # Load .torrent file into libtorrent
    ses = lt.session()
    info = lt.torrent_info(filename)
    save_dir = os.path.join('.', info.name())
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    handle = ses.add_torrent({'ti': info, 'save_path': save_dir})
    print(f"Starting torrent download for: {info.name()}")

    progress_bar = tqdm(total=info.total_size(), unit='iB', unit_scale=True, desc=info.name())
    while not handle.is_seed():
        status = handle.status()
        progress_bar.update(int(status.progress * info.total_size()) - progress_bar.n)
        progress_bar.set_postfix_str(f"Download Speed: {status.download_rate / 1024:.2f} kB/s")
        time.sleep(1)

    progress_bar.close()
    print(f"Torrent download complete: {info.name()}")

    return save_dir  # Return the path of the downloaded torrent folder

# Function to handle torrent download logic
def torrent_download_manager():
    torrent_type = ask_for_torrent_type()

    if torrent_type == '1':  # Magnet URI
        magnet_link = input("Enter the Magnet URI: ")
        return download_torrent_magnet(magnet_link)

    elif torrent_type == '2':  # .torrent file upload
        torrent_file = input("Provide the path to the .torrent file: ")
        return download_torrent_file(torrent_file, is_url=False)

    elif torrent_type == '3':  # .torrent file download link
        torrent_link = input("Enter the URL for the .torrent file: ")
        return download_torrent_file(torrent_link, is_url=True)

# Function to ask the user if they want to upload the file to Mega.nz
def ask_for_upload(file_path):
    choice = input(f"Do you want to upload {file_path} to Mega.nz? (y/n): ").lower()
    if choice == 'y':
        upload_to_mega(file_path)
    else:
        print(f"File {file_path} will not be uploaded.")

# Function to manage both direct and torrent downloads
def download_manager():
    is_torrent = ask_for_download_type()

    if is_torrent:
        download_path = torrent_download_manager()
        ask_for_upload(download_path)
    else:
        url = input('Provide URL of the File: ')
        filename = extract_filename_from_url_or_magnet(url)
        download_file(url, filename)
        ask_for_upload(filename)

if __name__ == "__main__":
    download_manager()
