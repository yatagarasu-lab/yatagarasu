# services/dropbox_uploader.py

import dropbox
import hashlib
import os
from io import BytesIO

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

if not all([DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_REFRESH_TOKEN]):
    raise EnvironmentError("Dropboxの認証情報が不足しています")

dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

def list_files(folder_path="/Apps/slot-data-analyzer"):
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"[Dropbox] フォルダ一覧取得失敗: {e}")
        return []

def download_file(path):
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"[Dropbox] ダウンロード失敗: {e}")
        return None

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        if content is None:
            continue

        hash_value = file_hash(content)
        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # dbx.files_delete_v2(path)  # 本番環境で使うときはコメントを外す
        else:
            hash_map[hash_value] = path

    print("✅ 重複チェック完了")
