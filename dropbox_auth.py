import os
import dropbox

def get_dropbox_client():
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
    app_key = os.getenv("DROPBOX_CLIENT_ID")
    app_secret = os.getenv("DROPBOX_CLIENT_SECRET")

    if not all([refresh_token, app_key, app_secret]):
        raise ValueError("Dropbox環境変数が未設定です")

    return dropbox.Dropbox(
        oauth2_refresh_token=refresh_token,
        app_key=app_key,
        app_secret=app_secret
    )