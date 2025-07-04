# dropbox_handler.py

import dropbox
from dropbox.files import WriteMode
from dropbox_auth import get_access_token
import hashlib

def get_dbx():
    access_token = get_access_token()
    return dropbox.Dropbox(access_token)

def upload_file(file_path, dropbox_path):
    dbx = get_dbx()
    with open(file_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=WriteMode("overwrite"))

def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dbx()
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    dbx = get_dbx()
    _, res = dbx.files_download(path)
    return res.content

def delete_file(path):
    dbx = get_dbx()
    dbx.files_delete_v2(path)

def file_hash(content):
    return hashlib.sha256(content).hexdigest()