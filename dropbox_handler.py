import os
import io
import zipfile
import dropbox
import hashlib
from dotenv import load_dotenv

load_dotenv()

# Dropbox認証情報
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

def get_dropbox_instance():
    return dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )

dbx = get_dropbox_instance()

def upload_to_dropbox(data: bytes, path: str):
    dbx.files_upload(data, path, mode=dropbox.files.WriteMode.overwrite)

def upload_zip_to_dropbox(filename: str, binary_data: bytes, dropbox_path: str):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(filename, binary_data)
    zip_buffer.seek(0)
    dbx.files_upload(zip_buffer.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)

def list_files(folder_path: str):
    return dbx.files_list_folder(folder_path).entries

def download_file(path: str) -> bytes:
    metadata, res = dbx.files_download(path)
    return res.content

def delete_file(path: str):
    dbx.files_delete_v2(path)

def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def find_and_remove_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)
        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            delete_file(path)
        else:
            hash_map[hash_value] = path