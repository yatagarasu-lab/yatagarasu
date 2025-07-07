import os
import dropbox
import hashlib
import requests
from io import BytesIO

# 環境変数からDropbox App情報を取得
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

FOLDER_PATH = "/Apps/slot-data-analyzer"

# ✅ リフレッシュトークンからアクセストークンを取得する関数
def get_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET,
    }

    response = requests.post(url, data=data)
    if response.status_code != 200:
        raise Exception(f"アクセストークンの取得に失敗しました: {response.text}")
    return response.json()["access_token"]

# ✅ Dropboxオブジェクトを毎回作成する関数
def get_dropbox():
    access_token = get_access_token()
    return dropbox.Dropbox(access_token)

# ✅ 指定フォルダ内のファイル一覧を取得
def list_files(folder_path=FOLDER_PATH):
    dbx = get_dropbox()
    res = dbx.files_list_folder(folder_path)
    return res.entries

# ✅ ファイルをダウンロードして内容を返す
def download_file(path):
    dbx = get_dropbox()
    _, res = dbx.files_download(path)
    return res.content

# ✅ 内容のハッシュ（重複判定用）
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# ✅ 重複ファイルを探して削除（オプション）
def find_duplicates(folder_path=FOLDER_PATH):
    dbx = get_dropbox()
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # 重複ファイルを削除したい場合は以下を有効化
            # dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path