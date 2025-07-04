# dropbox_auth.py
import os
import requests
import time

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

_cached_token = None
_cached_expiry = 0

def get_dropbox_access_token():
    global _cached_token, _cached_expiry

    if _cached_token and time.time() < _cached_expiry - 60:
        return _cached_token

    url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
    }

    auth = (DROPBOX_APP_KEY, DROPBOX_APP_SECRET)

    response = requests.post(url, data=data, auth=auth)

    if response.status_code == 200:
        token_info = response.json()
        _cached_token = token_info["access_token"]
        _cached_expiry = time.time() + token_info.get("expires_in", 14400)  # 4時間デフォルト
        return _cached_token
    else:
        raise Exception(f"Dropbox access token refresh failed: {response.status_code}, {response.text}")