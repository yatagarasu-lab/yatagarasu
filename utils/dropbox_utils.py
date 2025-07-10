import os
import dropbox
from dropbox.files import WriteMode
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from io import BytesIO
import hashlib
import base64
import requests
from datetime import datetime, timedelta

DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

DROPBOX_ROOT_PATH = "/Apps/slot-data-analyzer"

def get_dropbox_access_token():
    """リフレッシュトークンからアクセストークンを取得"""
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_APP_KEY,
        "client_secret": DROPBOX_APP_SECRET
    }
    response = requests.post(url, data=data)
    if response.status_code != 200:
        raise Exception("Dropboxアクセストークン取得に失敗しました")
    return response.json()["access_token"]

def get_dropbox_client():
    access_token = get_dropbox_access_token()
    return dropbox.Dropbox(access_token)

def list_files(folder_path=DROPBOX_ROOT_PATH):
    dbx = get_dropbox_client()
    result = dbx.files_list_folder(folder_path)
    return result.entries

def download_file(path):
    dbx = get_dropbox_client()
    metadata, res = dbx.files_download(path)
    return res.content

def file_hash(content):
    """ファイルのハッシュ値（SHA256）を返す"""
    return hashlib.sha256(content).hexdigest()

def delete_file(path):
    dbx = get_dropbox_client()
    dbx.files_delete_v2(path)

def upload_file(file_bytes, path):
    dbx = get_dropbox_client()
    dbx.files_upload(file_bytes, path, mode=WriteMode("overwrite"))