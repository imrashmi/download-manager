# Multi-Source Download and Upload Manager

This Python script provides a unified interface for downloading files from various sources, including direct URLs, torrents (magnet URI and `.torrent` files), YouTube videos, YouTube playlists, and Google Drive. It also supports uploading downloaded files to Mega.nz for storage and sharing.

## Features

1. **Direct File Download**: Download any file from a direct URL with progress tracking, time taken, and automatic retries.
2. **Google Drive Public Link Download**: Download files from public Google Drive links.
3. **YouTube Video Download**: Download individual YouTube videos in the highest resolution available.
4. **YouTube Playlist Download**: Download entire YouTube playlists, with sequential naming and automatic skipping of unavailable/private videos.
5. **Torrent Download**: Supports downloading via magnet URIs and `.torrent` files. Downloads are done with status tracking and retry mechanisms.
6. **Mega.nz Upload**: After the download is complete, the user is prompted to upload the file to Mega.nz with an automatically generated shareable link.

## Dependencies

The following Python libraries are required:

- `requests`: For making HTTP requests and handling direct downloads.
- `tqdm`: For displaying a progress bar during file downloads.
- `pytube`: For downloading videos and playlists from YouTube.
- `google-auth`, `google-auth-oauthlib`, `google-auth-httplib2`, `google-api-python-client`: For accessing Google Drive files via public links.
- `mega.py`: For uploading files to Mega.nz.
- `libtorrent`: For handling torrent downloads.

You can install all the dependencies using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

## Usage

1. **Run the Script**

   Execute the Python script using the following command:

   ```bash
   python mainscript.py
   ```

2. **Select Download Type**

   You will be prompted to choose between the following download types:
   
   - **Direct Download**: Download a file from any URL.
   - **Torrent Download**: Download via a magnet URI or a `.torrent` file.
   - **YouTube Download**: Download a YouTube video or a playlist.
   - **Google Drive Download**: Download files using a public Google Drive link.

3. **Upload to Mega.nz**

   After a download is completed, the script will ask if you want to upload the file to Mega.nz. If you agree, the file will be uploaded, and a shareable link will be generated.

### Detailed Steps

#### 1. Direct File Download

   - Input the URL of the file you want to download.
   - The script will automatically extract the file name and download it.
   - You will see a progress bar with download speed and estimated time remaining.
   - After download completion, you will be asked if you want to upload the file to Mega.nz.

#### 2. Torrent Download

   - Choose between:
     - **Magnet URI**: Input the magnet URI for the torrent.
     - **.torrent file**: Input the path to the `.torrent` file or provide a URL to download the `.torrent` file.
   - The torrent download will begin with a progress bar, download speed, and percentage complete.
   - Once completed, you will be prompted to upload the downloaded files to Mega.nz.

#### 3. YouTube Video or Playlist Download

   - For individual YouTube videos, input the URL of the video.
   - For playlists, input the playlist URL. The script will download all available videos sequentially, renaming them by prepending the serial number.
   - The script will skip any private or unavailable videos and report them at the end.

#### 4. Google Drive Public Link Download

   - Input the Google Drive public link.
   - The file will be downloaded, and a progress bar will track the download.
   - Once completed, you will be prompted to upload the file to Mega.nz.

## Configuration

### Mega.nz Account

For the Mega.nz upload functionality, you can store your Mega account credentials in environment variables:

```bash
export MEGA_EMAIL='your_email@example.com'
export MEGA_PASSWORD='your_password'
```

Alternatively, the script will prompt you for Mega.nz login credentials during runtime if the environment variables are not set.

## License
This project is licensed under the GNU General Public License v3.0. You are free to modify and distribute this software, but any derivative work must also be licensed under the same terms.

See the LICENSE file for more details.

```
