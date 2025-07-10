import os
import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox.files import WriteMode
from dropbox.oauth import OAuth2FlowResult
from dropbox import DropboxOAuth2Flow

def get_dbx_client():
    """リフレッシュトークンを使ってDropboxクライアントを取得"""
    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")

    if not all([app_key, app_secret, refresh_token]):
        raise Exception("Dropboxの認証情報が不足しています。")

    dbx = dropbox.Dropbox(
        oauth2_refresh_token=refresh_token,
        app_key=app_key,
        app_secret=app_secret
    )
    return dbx
