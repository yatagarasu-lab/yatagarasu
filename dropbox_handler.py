import dropbox
import os
from dropbox.oauth import DropboxOAuth2FlowNoRedirect

# 環境変数から取得
APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

def get_dropbox_client():
    oauth2_refresh_flow = dropbox.DropboxOAuth2FlowNoRedirect(APP_KEY, APP_SECRET)
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=REFRESH_TOKEN,
        app_key=APP_KEY,
        app_secret=APP_SECRET
    )
    return dbx