# services/dropbox_uploader.py

import dropbox
import hashlib
import os

def get_dropbox_client():
    DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
    DROPBOX_APP_KEY = os.getenv("DROPBOX_CLIENT_ID")
    DROPBOX_APP_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

    if not all([DROPBOX_REFRESH_TOKEN, DROPBOX_APP_KEY, DROPBOX_APP_SECRET]):
        raise EnvironmentError("Dropboxの認証情報が不足しています。")

    return dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )

def list_files(folder_path="/Apps/slot-data-analyzer"):
    try:
        dbx = get_dropbox_client()
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"[Dropbox] フォルダー一覧取得失敗: {e}")
        return []

def download_file(path):
    try:
        dbx = get_dropbox_client()
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"[Dropbox] ファイルダウンロード失敗: {e}")
        return None

def file_hash(content):
    return hashlib.sha256(content).hexdigest()