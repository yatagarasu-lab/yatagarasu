import os
import dropbox
import hashlib

DROPBOX_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

dbx = dropbox.Dropbox(DROPBOX_TOKEN)

def upload_file(filename, content_bytes):
    path = f"{DROPBOX_FOLDER}/{filename}"
    dbx.files_upload(content_bytes, path, mode=dropbox.files.WriteMode("overwrite"))

def list_files(folder_path=DROPBOX_FOLDER):
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox list_files エラー: {e}")
        return []

def download_file(path):
    try:
        _, res = dbx.files_download(path)
        return res.content
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox download_file エラー: {e}")
        return None

def file_hash(content_bytes):
    return hashlib.sha256(content_bytes).hexdigest()

def find_duplicates(folder_path=DROPBOX_FOLDER):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        if content is None:
            continue

        hash_value = file_hash(content)
        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            dbx.files_delete_v2(path)  # 重複を自動削除
        else:
            hash_map[hash_value] = path