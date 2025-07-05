import dropbox
import hashlib
import os

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def list_files(folder_path="/Apps/slot-data-analyzer"):
    try:
        res = dbx.files_list_folder(folder_path)
        return res.entries
    except Exception as e:
        print(f"リスト取得エラー: {e}")
        return []

def download_file(path):
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"ダウンロードエラー: {e}")
        return None

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    duplicates = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        if content is None:
            continue
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            dbx.files_delete_v2(path)
            duplicates.append(path)
        else:
            hash_map[hash_value] = path

    return duplicates

def clean_old_files(folder_path="/Apps/slot-data-analyzer", keep=10):
    files = sorted(list_files(folder_path), key=lambda f: f.server_modified, reverse=True)
    old_files = files[keep:]
    for file in old_files:
        try:
            dbx.files_delete_v2(file.path_display)
            print(f"古いファイル削除: {file.path_display}")
        except Exception as e:
            print(f"削除失敗: {file.path_display} - {e}")