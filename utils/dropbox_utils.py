import os
import dropbox
import hashlib
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# リフレッシュトークンでアクセストークン取得
def get_access_token():
    import requests
    res = requests.post(
        "https://api.dropbox.com/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
            "client_id": APP_KEY,
            "client_secret": APP_SECRET,
        },
    )
    return res.json()["access_token"]

# クライアント取得
def get_dropbox_client():
    token = get_access_token()
    return dropbox.Dropbox(token)

# ファイルの一覧取得（軽量用）
def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    try:
        res = dbx.files_list_folder(folder_path)
        return res.entries
    except Exception as e:
        print("Dropbox list_files error:", e)
        return []

# ファイルのダウンロード
def download_file(path):
    dbx = get_dropbox_client()
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print("Dropbox download error:", e)
        return None

# ファイルアップロード（内容が同一でも上書き保存）
def upload_file(path, content_bytes):
    dbx = get_dropbox_client()
    try:
        dbx.files_upload(content_bytes, path, mode=dropbox.files.WriteMode.overwrite)
        print(f"Uploaded: {path}")
    except Exception as e:
        print("Dropbox upload error:", e)

# SHA256で内容のハッシュ取得
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# 重複ファイル検出（ハッシュで）
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    dbx = get_dropbox_client()

    for file in files:
        path = file.path_display
        content = download_file(path)
        if not content:
            continue
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            try:
                dbx.files_delete_v2(path)
                print(f"削除済み: {path}")
            except Exception as e:
                print(f"削除失敗: {path} → {e}")
        else:
            hash_map[hash_value] = path