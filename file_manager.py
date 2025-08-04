import os
import hashlib
import dropbox
from dropbox.files import FileMetadata

DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
DROPBOX_TARGET_FOLDER = "/Apps/slot-data-analyzer"

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def list_files(folder_path=DROPBOX_TARGET_FOLDER):
    entries = []
    result = dbx.files_list_folder(folder_path)
    entries.extend(result.entries)
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        entries.extend(result.entries)
    return [entry for entry in entries if isinstance(entry, FileMetadata)]

def find_latest_file(files):
    latest_file = max(files, key=lambda x: x.client_modified)
    return latest_file

def delete_duplicates(files):
    hash_map = {}
    for file in files:
        path = file.path_display
        _, res = dbx.files_download(path)
        content = res.content
        hash_value = file_hash(content)
        if hash_value in hash_map:
            print(f"🗑️ 重複ファイル削除: {path}")
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

def organize_dropbox_files():
    files = list_files()
    if not files:
        print("⚠️ Dropboxにファイルがありません。")
        return None

    delete_duplicates(files)
    latest_file = find_latest_file(files)
    print(f"📦 最新ファイル: {latest_file.name}")
    return latest_file