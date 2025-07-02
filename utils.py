import os
import dropbox
from dropbox.exceptions import AuthError
from dotenv import load_dotenv

load_dotenv()

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

def get_dropbox_client():
    try:
        dbx = dropbox.Dropbox(
            app_key=DROPBOX_APP_KEY,
            app_secret=DROPBOX_APP_SECRET,
            oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
        )
        return dbx
    except AuthError as e:
        print("Dropbox認証エラー:", e)
        return None

def list_files_in_folder(folder_path="/スロットデータ"):
    dbx = get_dropbox_client()
    if not dbx:
        return []

    try:
        result = dbx.files_list_folder(folder_path)
        return [entry.name for entry in result.entries if isinstance(entry, dropbox.files.FileMetadata)]
    except Exception as e:
        print(f"Dropboxフォルダ取得失敗: {e}")
        return []

def download_file(file_path):
    dbx = get_dropbox_client()
    if not dbx:
        return None

    try:
        metadata, res = dbx.files_download(file_path)
        return res.content
    except Exception as e:
        print(f"Dropboxファイルダウンロード失敗: {e}")
        return None