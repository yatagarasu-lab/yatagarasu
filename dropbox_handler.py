import dropbox
import hashlib
from io import BytesIO
import os

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_files(folder_path="/Apps/slot-data-analyzer"):
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox list error: {e}")
        return []

def download_file(path):
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"Dropbox download error: {e}")
        return None

def upload_file(data: bytes, path: str):
    try:
        dbx.files_upload(data, path, mode=dropbox.files.WriteMode.overwrite)
        print(f"Uploaded to {path}")
    except Exception as e:
        print(f"Dropbox upload error: {e}")

def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        if not content:
            continue

        hash_value = file_hash(content)
        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # 重複ファイルを削除したい場合は以下を有効に
            # dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path