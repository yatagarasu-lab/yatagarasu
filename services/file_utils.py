import dropbox
import os
from io import BytesIO

# 環境変数から直接取得（config.py は一切使わない）
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

# チェック：環境変数が全て設定されているか
if not all([DROPBOX_REFRESH_TOKEN, DROPBOX_APP_KEY, DROPBOX_APP_SECRET]):
    raise EnvironmentError("Dropboxの認証情報が不足しています。")

# Dropbox認証
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

def list_dropbox_files(folder_path=""):
    try:
        response = dbx.files_list_folder(path=folder_path)
        return [entry.path_display for entry in response.entries]
    except Exception as e:
        print(f"[Dropbox] フォルダー一覧取得失敗: {e}")
        return []

def download_dropbox_file(path):
    try:
        metadata, res = dbx.files_download(path)
        return res.content.decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"[Dropbox] ファイルダウンロード失敗: {e}")
        return None