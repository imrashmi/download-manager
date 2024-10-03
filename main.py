import os
import requests
from tqdm import tqdm
from urllib.parse import urlparse, parse_qs, unquote
import time
import libtorrent as lt
from pytube import YouTube, Playlist
import google.auth
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
from mega import Mega

# Function to extract file name and extension from URL
def extract_filename_from_url(url):
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    return unquote(filename)  # Decode URL-encoded characters

# Function to extract file ID from Google Drive public link
def extract_google_drive_file_id(drive_link):
    parsed_url = urlparse(drive_link)
    query_params = parse_qs(parsed_url.query)
    
    if 'id' in query_params:
        return query_params['id'][0]
    elif '/file/d/' in drive_link:
        return drive_link.split('/file/d/')[1].split('/')[0]
    else:
        raise ValueError("Invalid Google Drive link format.")

# Function to download files from Google Drive using a public link
def download_google_drive_file(file_id, filename):
    creds, _ = google.auth.default()
    service = build('drive', 'v3', credentials=creds)
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(filename, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    with tqdm(total=100, desc=f"Downloading {filename}", unit='%') as pbar:
        while not done:
            status, done = downloader.next_chunk()
            pbar.update(status.progress() * 100)
    fh.close()

# Function to download YouTube video
def download_youtube_video(url):
    yt = YouTube(url)
    video = yt.streams.get_highest_resolution()
    filename = video.default_filename
    video.download(filename=filename)
    print(f"\nDownload complete: {filename}")
    return filename

# Function to download YouTube playlist
def download_youtube_playlist(playlist_url):
    playlist = Playlist(playlist_url)
    playlist_folder = playlist.title
    if not os.path.exists(playlist_folder):
        os.makedirs(playlist_folder)
    skipped_videos = []
    print(f"\nDownloading playlist: {playlist.title}")

    for i, video in enumerate(playlist.videos):
        try:
            video_filename = video.streams.get_highest_resolution().default_filename
            video.streams.get_highest_resolution().download(output_path=playlist_folder)
            os.rename(os.path.join(playlist_folder, video_filename),
                      os.path.join(playlist_folder, f"{i + 1:02d}_{video.title}.mp4"))
            print(f"Downloaded: {video.title}")
        except Exception as e:
            skipped_videos.append((i + 1, video.title))
            print(f"Skipped: {video.title} - {e}")

    if skipped_videos:
        print("\nSkipped videos:")
        for serial, title in skipped_videos:
            print(f"Serial {serial}: {title}")

# Function to handle file downloading
def download_file(url, filename, chunk_size=1024):
    start_time = time.time()  # Start timing the download
    resume_header = {}
    mode = 'wb'  # default write mode

    if os.path.exists(filename):
        resume_header = {'Range': f'bytes={os.path.getsize(filename)}-'}
        mode = 'ab'  # append mode

    with requests.get(url, headers=resume_header, stream=True) as r:
        total_size = int(r.headers.get('content-length', 0))
        progress_bar = tqdm(
            total=total_size,
            unit='iB',
            unit_scale=True,
            initial=os.path.getsize(filename) if os.path.exists(filename) else 0,
            desc=filename,
            dynamic_ncols=True,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
        )

        with open(filename, mode) as f:
            for chunk in r.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    progress_bar.update(len(chunk))
        progress_bar.close()

    elapsed_time = time.time() - start_time
    print(f"\nFile {filename} downloaded in {time.strftime('%H:%M:%S', time.gmtime(elapsed_time))}")

# Function for torrent download
def download_torrent(magnet_link, save_path):
    ses = lt.session()
    params = {
        'save_path': save_path,
        'storage_mode': lt.storage_mode_t.storage_mode_sparse
    }
    handle = lt.add_magnet_uri(ses, magnet_link, params)
    print("\nFetching metadata...")
    while not handle.has_metadata():
        time.sleep(1)

    print("Downloading started!")
    while not handle.is_seed():
        status = handle.status()
        print(f"\rDownloaded {status.progress * 100:.2f}% "
              f"({status.total_done / 1024 / 1024:.2f} MB) at {status.download_rate / 1024:.2f} KB/s",
              end="")
        time.sleep(1)

    print("\nTorrent download complete!")

# Mega.nz upload function
def upload_to_mega(filename):
    mega = Mega()
    email = os.getenv('MEGA_EMAIL')
    password = os.getenv('MEGA_PASSWORD')

    m = mega.login(email, password) if email and password else mega.login()
    print("\nUploading file to Mega.nz...")
    file = m.upload(filename)
    link = m.get_upload_link(file)
    print(f"Upload complete! Shareable link: {link}")

# Main download manager
def download_manager():
    print("Select download type:\n1. Direct Download\n2. Torrent Download\n3. YouTube Download\n4. Google Drive Download")
    choice = input("Enter your choice: ")

    if choice == '1':  # Direct download
        url = input('Provide URL of File: ')
        filename = extract_filename_from_url(url)
        download_file(url, filename)
        if input("Do you want to upload the file to Mega.nz? (y/n): ").lower() == 'y':
            upload_to_mega(filename)

    elif choice == '2':  # Torrent download
        torrent_choice = input("Select torrent type:\n1. Magnet URI\n2. .torrent file\n3. Torrent URL\nEnter choice: ")
        if torrent_choice == '1':
            magnet_uri = input("Enter Magnet URI: ")
            save_path = input("Enter download folder: ")
            download_torrent(magnet_uri, save_path)

        elif torrent_choice == '2':
            torrent_file = input("Enter path to .torrent file: ")
            save_path = input("Enter download folder: ")
            download_torrent_from_file(torrent_file, save_path)

        elif torrent_choice == '3':
            url = input("Enter URL to .torrent file: ")
            torrent_file = extract_filename_from_url(url)
            download_file(url, torrent_file)
            save_path = input("Enter download folder: ")
            download_torrent_from_file(torrent_file, save_path)

        if input("Do you want to upload the downloaded files to Mega.nz? (y/n): ").lower() == 'y':
            upload_to_mega(save_path)

    elif choice == '3':  # YouTube download
        yt_choice = input("1. YouTube Video\n2. YouTube Playlist\nEnter your choice: ")
        if yt_choice == '1':
            url = input("Enter YouTube video URL: ")
            filename = download_youtube_video(url)
            if input("Do you want to upload the file to Mega.nz? (y/n): ").lower() == 'y':
                upload_to_mega(filename)
        elif yt_choice == '2':
            url = input("Enter YouTube playlist URL: ")
            download_youtube_playlist(url)

    elif choice == '4':  # Google Drive download
        drive_link = input("Enter Google Drive public link: ")
        file_id = extract_google_drive_file_id(drive_link)
        filename = input("Enter filename to save as: ")
        download_google_drive_file(file_id, filename)
        if input("Do you want to upload the file to Mega.nz? (y/n): ").lower() == 'y':
            upload_to_mega(filename)

if __name__ == "__main__":
    download_manager()
