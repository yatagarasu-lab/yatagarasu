import os
import json
import requests
import dropbox

# 環境変数から各種キーを取得
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

# アクセストークン取得（自動更新）
def get_access_token():
    url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET,
    }

    response = requests.post(url, data=data)
    if response.status_code == 200:
        token_info = response.json()
        return token_info["access_token"]
    else:
        raise Exception(f"アクセストークンの取得に失敗しました: {response.text}")

# Dropboxクライアント作成
def get_dropbox_client():
    access_token = get_access_token()
    return dropbox.Dropbox(access_token)

# 指定フォルダ内のファイル一覧取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    res = dbx.files_list_folder(folder_path)
    return res.entries

# ファイルのダウンロード
def download_file(path):
    dbx = get_dropbox_client()
    _, res = dbx.files_download(path)
    return res.content

# ファイルのアップロード（必要なら）
def upload_file(local_path, dropbox_path):
    dbx = get_dropbox_client()
    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)

# ファイルの削除（重複対策などで使用）
def delete_file(dropbox_path):
    dbx = get_dropbox_client()
    dbx.files_delete_v2(dropbox_path)