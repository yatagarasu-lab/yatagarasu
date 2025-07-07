import os
import dropbox
import requests
import json
import hashlib

# 環境変数から取得
APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# アクセストークンをリフレッシュする関数
def get_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": APP_KEY,
        "client_secret": APP_SECRET
    }
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"アクセストークン取得失敗: {response.text}")

# Dropboxインスタンス作成
def get_dbx():
    access_token = get_access_token()
    return dropbox.Dropbox(access_token)

# ファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dbx()
    res = dbx.files_list_folder(folder_path)
    return res.entries

# ファイルのダウンロード
def download_file(path):
    dbx = get_dbx()
    _, res = dbx.files_download(path)
    return res.content

# ファイルのSHA256ハッシュ値を取得
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# 重複ファイルをチェック（同一ハッシュ）
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"🔁 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # dbx = get_dbx()
            # dbx.files_delete_v2(path)  # 削除したい場合はこちらを有効化
        else:
            hash_map[hash_value] = path