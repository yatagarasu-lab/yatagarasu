import dropbox
import hashlib
import os

ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(ACCESS_TOKEN)

def list_files(folder_path="/Apps/slot-data-analyzer"):
    return dbx.files_list_folder(folder_path).entries

def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

def delete_file(path):
    dbx.files_delete_v2(path)

def file_hash(content):
    return hashlib.md5(content).hexdigest()