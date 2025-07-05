import dropbox
import os
import hashlib
from datetime import datetime

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
FOLDER_PATH = "/Apps/slot-data-analyzer"

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def save_uploaded_file(data, extension="txt"):
    # 一意のファイル名を生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{FOLDER_PATH}/{timestamp}.{extension}"
    dbx.files_upload(data, filename, mode=dropbox.files.WriteMode("overwrite"))
    return filename

def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

def file_hash(data):
    return hashlib.sha256(data).hexdigest()

def find_duplicates():
    files = dbx.files_list_folder(FOLDER_PATH).entries
    hash_map = {}

    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            path = file.path_display
            content = download_file(path)
            h = file_hash(content)

            if h in hash_map:
                print(f"重複ファイル検出: {path} == {hash_map[h]}")
                # dbx.files_delete_v2(path)  # 削除する場合はコメント解除
            else:
                hash_map[h] = path