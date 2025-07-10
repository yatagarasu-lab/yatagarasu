import os
import json
import requests
import dropbox
from dotenv import load_dotenv

load_dotenv()

DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

def get_dropbox_client_with_refresh() -> dropbox.Dropbox:
    """Dropboxのアクセストークンをリフレッシュしてクライアントを返す"""
    token_url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET,
    }

    response = requests.post(token_url, data=data)
    response.raise_for_status()

    access_token = response.json()["access_token"]
    return dropbox.Dropbox(access_token)


def list_files(folder_path: str, dbx: dropbox.Dropbox):
    """Dropbox内のファイルを一覧取得"""
    try:
        res = dbx.files_list_folder(folder_path)
        files = res.entries
        while res.has_more:
            res = dbx.files_list_folder_continue(res.cursor)
            files.extend(res.entries)
        return [f for f in files if isinstance(f, dropbox.files.FileMetadata)]
    except Exception as e:
        print(f"[list_files エラー] {e}")
        return []


def download_file(file_path: str, dbx: dropbox.Dropbox) -> bytes:
    """Dropboxのファイルをバイナリで取得"""
    _, res = dbx.files_download(file_path)
    return res.content


def move_file(from_path: str, to_path: str, dbx: dropbox.Dropbox):
    """Dropbox内でファイルを移動（分類フォルダへ）"""
    try:
        dbx.files_move_v2(from_path, to_path, allow_shared_folder=True, autorename=True)
    except dropbox.exceptions.ApiError as e:
        print(f"[move_file エラー] {e}")