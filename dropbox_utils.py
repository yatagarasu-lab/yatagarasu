import dropbox
import os

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
FOLDER_PATH = "/Apps/slot-data-analyzer"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_files(folder_path=FOLDER_PATH):
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content