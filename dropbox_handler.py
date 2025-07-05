import os
import dropbox
from hashlib import md5
from datetime import datetime

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_files(folder_path=DROPBOX_FOLDER_PATH):
    files = []
    try:
        result = dbx.files_list_folder(folder_path)
        files.extend(result.entries)
        while result.has_more:
            result = dbx.files_list_folder_continue(result.cursor)
            files.extend(result.entries)
    except Exception as e:
        print(f"[list_files] Error: {e}")
    return files

def download_file(path):
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"[download_file] Error: {e}")
        return None