# dropbox_utils.py
import dropbox
import os
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError
from dropbox_auth import get_dropbox_access_token

def get_dropbox_client():
    access_token = get_dropbox_access_token()
    return dropbox.Dropbox(oauth2_access_token=access_token)

def upload_file(file_path, dropbox_path):
    dbx = get_dropbox_client()
    with open(file_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=WriteMode("overwrite"))

def download_file(dropbox_path):
    dbx = get_dropbox_client()
    metadata, res = dbx.files_download(dropbox_path)
    return res.content

def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except ApiError as e:
        print(f"Dropbox list_files error: {e}")
        return []

def file_hash(content):
    import hashlib
    return hashlib.sha256(content).hexdigest()

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # dbx = get_dropbox_client()
            # dbx.files_delete_v2(path)  # 重複削除するなら有効化
        else:
            hash_map[hash_value] = path