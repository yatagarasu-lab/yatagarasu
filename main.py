from flask import Flask, request
import dropbox
import hashlib
import os
import requests
from datetime import datetime
import json

app = Flask(__name__)

# ======================
# ▼設定（ユーザーごとに変更）
# ======================
LINE_USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

DROPBOX_CLIENT_ID = os.environ.get("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.environ.get("DROPBOX_CLIENT_SECRET")
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")

DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"

# ======================
# ▼リフレッシュトークン方式でアクセストークン取得
# ======================
def get_dropbox_access_token():
    url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# ======================
# ▼Dropbox操作系
# ======================
def list_files(folder_path):
    access_token = get_dropbox_access_token()
    dbx = dropbox.Dropbox(access_token)
    result = dbx.files_list_folder(folder_path)
    return result.entries

def download_file(path):
    access_token = get_dropbox_access_token()
    dbx = dropbox.Dropbox(access_token)
    metadata, res = dbx.files_download(path)
    return res.content

def delete_file(path):
    access_token = get_dropbox_access_token()
    dbx = dropbox.Dropbox(access_token)
    dbx.files_delete_v2(path)

# ======================
# ▼重複チェック用ハッシュ
# ======================
def file_hash(content):
    return hashlib.md5(content).hexdigest()

def find_duplicates(folder_path=DROPBOX_FOLDER_PATH):
    files = list_files(folder_path)
    hash_map = {}
    deleted_files = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            delete_file(path)
            deleted_files.append(path)
        else:
            hash_map[hash_value] = path

    return deleted_files

# ======================
# ▼LINE通知
# ======================
def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()

# ======================
# ▼Webhookエンドポイント
# ======================
@app.route("/", methods=["GET", "POST"])
def webhook():
    try:
        deleted = find_duplicates()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if deleted:
            msg = f"[{now}] 重複ファイルを削除しました:\n" + "\n".join(deleted)
        else:
            files = list_files(DROPBOX_FOLDER_PATH)
            latest_file = sorted(files, key=lambda x: x.server_modified)[-1]
            msg = f"[{now}] 新規ファイルを検出:\n{latest_file.name}"

        send_line_message(msg)
        return "OK", 200

    except Exception as e:
        send_line_message(f"エラー発生: {str(e)}")
        return str(e), 500