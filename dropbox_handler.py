import dropbox
import os
import hashlib

DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def upload_to_dropbox(data, path):
    dbx.files_upload(data, path, mode=dropbox.files.WriteMode.overwrite)

def list_files(folder_path):
    return dbx.files_list_folder(folder_path).entries

def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def delete_file(path):
    dbx.files_delete_v2(path)