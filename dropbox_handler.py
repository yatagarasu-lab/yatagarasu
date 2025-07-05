import dropbox
import hashlib
import io
import os
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox.exceptions import ApiError

DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

def get_dbx():
    return dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )

def download_file(path: str) -> bytes:
    """Dropbox上の指定パスのファイルをバイナリでダウンロード"""
    dbx = get_dbx()
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except ApiError as e:
        raise Exception(f"Dropbox download error: {e}")

def list_files(folder_path="/Apps/slot-data-analyzer") -> list:
    """指定フォルダ内のファイル一覧を取得"""
    dbx = get_dbx()
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except ApiError as e:
        raise Exception(f"Dropbox list error: {e}")

def file_hash(file_content: bytes) -> str:
    """ファイルの内容に基づくSHA256ハッシュを返す"""
    return hashlib.sha256(file_content).hexdigest()

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """重複ファイルを検出し、不要なファイルを削除（任意でON）"""
    dbx = get_dbx()
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # dbx.files_delete_v2(path)  # 自動削除したい場合はコメントを解除
        else:
            hash_map[hash_value] = path