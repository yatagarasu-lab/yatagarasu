import os
import requests

def get_dropbox_access_token():
    client_id = os.environ.get("DROPBOX_CLIENT_ID")
    client_secret = os.environ.get("DROPBOX_CLIENT_SECRET")
    refresh_token = os.environ.get("DROPBOX_REFRESH_TOKEN")

    if not client_id or not client_secret or not refresh_token:
        raise Exception("❌ Dropboxの環境変数が設定されていません。")

    url = "https://api.dropbox.com/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret
    }

    res = requests.post(url, headers=headers, data=data)
    if res.status_code != 200:
        raise Exception(f"❌ アクセストークン取得失敗: {res.text}")
    
    access_token = res.json().get("access_token")
    return access_token
