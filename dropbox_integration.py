import os
import dropbox
from requests_oauthlib import OAuth2Session

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

def get_dropbox_access_token():
    token_url = "https://api.dropbox.com/oauth2/token"

    response = OAuth2Session(client_id=DROPBOX_APP_KEY).refresh_token(
        token_url=token_url,
        refresh_token=DROPBOX_REFRESH_TOKEN,
        client_id=DROPBOX_APP_KEY,
        client_secret=DROPBOX_APP_SECRET
    )
    return response["access_token"]

def handle_dropbox_webhook():
    access_token = get_dropbox_access_token()
    dbx = dropbox.Dropbox(access_token)
    
    # 実際のファイル処理・通知などをここで実装
    print("Dropbox webhook handled.")
    return "OK", 200
