import dropbox
import hashlib
import os

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def download_file(path):
    """Dropbox からファイルをバイナリで取得"""
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        raise Exception(f"Dropbox ダウンロードエラー: {e}")

def list_files(folder_path="/Apps/slot-data-analyzer"):
    """Dropbox内のファイル一覧を取得"""
    try:
        res = dbx.files_list_folder(folder_path)
        return res.entries
    except Exception as e:
        raise Exception(f"Dropbox ファイル一覧取得エラー: {e}")

def file_hash(content):
    """ファイルの SHA256 ハッシュを取得"""
    return hashlib.sha256(content).hexdigest()

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """Dropbox フォルダ内の重複ファイルを検出・削除"""
    try:
        files = list_files(folder_path)
        hash_map = {}

        for file in files:
            path = file.path_display
            content = download_file(path)
            hash_value = file_hash(content)

            if hash_value in hash_map:
                print(f"重複ファイル削除: {path}")
                dbx.files_delete_v2(path)
            else:
                hash_map[hash_value] = path

    except Exception as e:
        raise Exception(f"重複チェックエラー: {e}")