import os
import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox.files import WriteMode

DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
FOLDER_PATH = "/Apps/slot-data-analyzer"

dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

def list_files(folder_path=FOLDER_PATH):
    return dbx.files_list_folder(folder_path).entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def file_hash(content):
    import hashlib
    return hashlib.sha256(content).hexdigest()