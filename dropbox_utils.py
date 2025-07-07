import os
import dropbox
import requests
import time

# 環境変数からリフレッシュトークンとアプリ情報を取得
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# キャッシュ（再認証を減らす）
_cached_token = None
_cached_token_time = 0

def get_access_token():
    global _cached_token, _cached_token_time

    # キャッシュが5分以内なら再利用
    if _cached_token and (time.time() - _cached_token_time < 300):
        return _cached_token

    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
    }
    auth = (DROPBOX_APP_KEY, DROPBOX_APP_SECRET)

    response = requests.post(url, data=data, auth=auth)
    response.raise_for_status()
    access_token = response.json()["access_token"]

    # キャッシュ更新
    _cached_token = access_token
    _cached_token_time = time.time()
    return access_token

# Dropbox接続
def get_dbx():
    token = get_access_token()
    return dropbox.Dropbox(token)

# ファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dbx()
    result = dbx.files_list_folder(folder_path)
    return result.entries

# ファイルをダウンロード
def download_file(path):
    dbx = get_dbx()
    metadata, response = dbx.files_download(path)
    return response.content