import os
import dropbox
import requests

# 環境変数から認証情報を取得
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# アクセストークンをリフレッシュトークンから取得
def get_dropbox_access_token():
    token_url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_APP_KEY,
        "client_secret": DROPBOX_APP_SECRET,
    }
    response = requests.post(token_url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# DropboxのWebhookイベントを処理（ファイル一覧を取得して表示）
def handle_dropbox_webhook():
    access_token = get_dropbox_access_token()
    dbx = dropbox.Dropbox(access_token)

    try:
        # Dropboxのルートディレクトリ内のファイルを取得
        result = dbx.files_list_folder(path="")

        print("=== Dropboxファイル一覧 ===")
        for entry in result.entries:
            print(f"- {entry.name}")
        print("===========================")

    except Exception as e:
        print(f"エラー: {e}")
        return "Internal Server Error", 500

    return "OK", 200