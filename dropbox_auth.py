# dropbox_auth.py
import os
import requests

DROPBOX_TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"

def get_access_token():
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")

    if not refresh_token or not app_key or not app_secret:
        raise ValueError("Dropboxの認証情報が不足しています。")

    response = requests.post(DROPBOX_TOKEN_URL, data={
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }, auth=(app_key, app_secret))

    if response.status_code != 200:
        raise Exception(f"アクセストークン更新失敗: {response.text}")

    return response.json()["access_token"]
