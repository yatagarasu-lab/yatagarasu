import dropbox
import os
import hashlib
from datetime import datetime

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

def upload_file(file_path, content):
    dbx.files_upload(content, file_path, mode=dropbox.files.WriteMode.overwrite)
    def save_to_dropbox(content, filename, folder="/Apps/slot-data-analyzer"):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    dropbox_path = f"{folder}/{now}_{filename}"
    upload_file(dropbox_path, content)
    return dropbox_path

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def remove_duplicate_files(folder="/Apps/slot-data-analyzer"):
    files = list_files(folder)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path
            def is_image(filename):
    return filename.lower().endswith((".jpg", ".jpeg", ".png"))

def is_text(filename):
    return filename.lower().endswith((".txt", ".csv"))

def list_and_filter_files(folder="/Apps/slot-data-analyzer"):
    all_files = list_files(folder)
    images = [f for f in all_files if is_image(f.name)]
    texts = [f for f in all_files if is_text(f.name)]
    return images, texts

def move_file_to_archive(path, archive_folder="/Apps/slot-data-analyzer/archive"):
    filename = os.path.basename(path)
    new_path = f"{archive_folder}/{filename}"
    dbx.files_move_v2(from_path=path, to_path=new_path)