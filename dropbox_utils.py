import os
import dropbox

# Dropboxの環境変数から各種キーを取得
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# Dropboxのクライアント初期化（リフレッシュトークン方式）
dbx = dropbox.Dropbox(
    oauth2_access_token=None,
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

def list_files(folder_path="/Apps/slot-data-analyzer"):
    try:
        res = dbx.files_list_folder(folder_path)
        return res.entries
    except Exception as e:
        print(f"📁 ファイル一覧取得エラー: {e}")
        return []

def download_file(path):
    try:
        _, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"📄 ファイルダウンロードエラー: {e}")
        return None