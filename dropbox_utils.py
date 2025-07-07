import os
import dropbox
import requests
from hashlib import sha256

# 環境変数から設定を取得
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_ACCESS_TOKEN = None  # 起動時にはトークンなし

# Dropboxインスタンス（アクセストークン更新で再作成）
dbx = None

def refresh_access_token():
    global DROPBOX_ACCESS_TOKEN, dbx
    print("🔄 アクセストークンを更新中...")
    url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_APP_KEY,
        "client_secret": DROPBOX_APP_SECRET,
    }

    response = requests.post(url, data=data)
    if response.status_code == 200:
        DROPBOX_ACCESS_TOKEN = response.json()["access_token"]
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        print("✅ アクセストークン更新完了")
    else:
        raise Exception(f"アクセストークンの更新に失敗: {response.text}")

def ensure_dbx():
    if dbx is None:
        refresh_access_token()

def list_files(folder_path):
    ensure_dbx()
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    ensure_dbx()
    metadata, response = dbx.files_download(path)
    return response.content

def file_hash(content):
    return sha256(content).hexdigest()