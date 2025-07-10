# utils/token_refresher.py

import os
import requests


def refresh_dropbox_access_token(refresh_token, app_key, app_secret):
    """Dropboxのアクセストークンをリフレッシュトークンから取得"""
    token_url = "https://api.dropboxapi.com/oauth2/token"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    response = requests.post(
        token_url,
        data=payload,
        auth=(app_key, app_secret),
    )

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Dropboxトークン更新失敗: {response.status_code} - {response.text}")
