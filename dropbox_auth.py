import requests
import os

def get_access_token():
    url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": os.getenv("DROPBOX_REFRESH_TOKEN"),
        "client_id": os.getenv("DROPBOX_CLIENT_ID"),
        "client_secret": os.getenv("DROPBOX_CLIENT_SECRET")
    }

    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]