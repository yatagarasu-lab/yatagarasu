import dropbox
from config import DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN
from io import BytesIO

dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

def list_dropbox_files(folder_path=""):
    response = dbx.files_list_folder(path=folder_path)
    return [entry.path_display for entry in response.entries if isinstance(entry, dropbox.files.FileMetadata)]

def download_dropbox_file(path):
    metadata, res = dbx.files_download(path)
    return res.content.decode('utf-8', errors='ignore')
