import os
import dropbox
import requests

def get_dropbox_access_token():
    """Refresh access token using Dropbox refresh token."""
    token_url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": os.getenv("DROPBOX_REFRESH_TOKEN"),
        "client_id": os.getenv("DROPBOX_APP_KEY"),
        "client_secret": os.getenv("DROPBOX_APP_SECRET")
    }
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        raise Exception(f"Failed to refresh token: {response.status_code} {response.text}")
    return response.json()["access_token"]

def get_dropbox_client():
    """Returns a Dropbox client authenticated with refreshed token."""
    access_token = get_dropbox_access_token()
    return dropbox.Dropbox(access_token)