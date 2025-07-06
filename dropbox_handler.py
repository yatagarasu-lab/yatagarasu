import dropbox
import os
from gpt_analyzer import analyze_file_and_notify, file_hash
from line_push import send_line_message

# 環境変数から取得（Renderに設定）
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")

# アクセストークンを取得
def get_access_token():
    from requests.auth import HTTPBasicAuth
    import requests

    url = "https://api.dropboxapi.com/oauth2/token"
    headers = {}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
    }
    auth = HTTPBasicAuth(DROPBOX_APP_KEY, DROPBOX_APP_SECRET)

    response = requests.post(url, headers=headers, data=data, auth=auth)
    return response.json().get("access_token")

# Dropboxインスタンス生成
def get_dropbox_client():
    token = get_access_token()
    return dropbox.Dropbox(token)

# フォルダ内のファイル一覧取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    result = dbx.files_list_folder(folder_path)
    return result.entries

# ファイルをダウンロード
def download_file(path):
    dbx = get_dropbox_client()
    metadata, res = dbx.files_download(path)
    return res.content

# Webhook受信時のイベント処理
def handle_dropbox_event():
    folder_path = "/Apps/slot-data-analyzer"
    files = list_files(folder_path)
    seen_hashes = {}

    for file in files:
        try:
            path = file.path_display
            content = download_file(path)
            hash_value = file_hash(content)

            # 重複ファイルチェック
            if hash_value in seen_hashes:
                dbx = get_dropbox_client()
                dbx.files_delete_v2(path)
                send_line_message(f"🗑️ 重複ファイルを削除しました: {path}")
            else:
                seen_hashes[hash_value] = path
                analyze_file_and_notify(path, content)
        except Exception as e:
            send_line_message(f"⚠️ Dropbox処理でエラー: {e}")