from flask import Flask, request, abort
import dropbox
import os
import hashlib
import requests

app = Flask(__name__)

# Dropbox設定（フルアクセス）
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

# GASスプレッドシートWebhook
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbyjfGpxEYHL3H1I0BYgJ86AVgpsUsE85pAPe4VcyijRbliKSpvguMhpTnhdZQ0YRwbC/exec"

def send_to_spreadsheet(source, message):
    payload = {
        "source": source,
        "message": message
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        print(f"✅ シート送信成功: {response.text}")
    except Exception as e:
        print(f"❌ シート送信エラー: {e}")

def get_dbx():
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox

    auth_flow = DropboxOAuth2FlowNoRedirect(DROPBOX_APP_KEY, DROPBOX_APP_SECRET)
    return Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )

def download_file(path):
    dbx = get_dbx()
    metadata, res = dbx.files_download(path)
    return res.content

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

@app.route("/", methods=["GET"])
def index():
    return "OK", 200

@app.route("/", methods=["POST"])
def webhook():
    try:
        dbx = get_dbx()
        print("📩 Dropbox Webhook Triggered")

        # ファイル一覧を取得
        result = dbx.files_list_folder(path="", recursive=False)
        files = result.entries

        hash_map = {}

        for file in files:
            if isinstance(file, dropbox.files.FileMetadata):
                path = file.path_display
                content = download_file(path)
                hash_value = file_hash(content)

                if hash_value in hash_map:
                    print(f"⚠️ 重複ファイル: {path}（同一: {hash_map[hash_value]}）")
                    dbx.files_delete_v2(path)
                else:
                    hash_map[hash_value] = path
                    print(f"📁 新規ファイル: {path}")

                    # 任意のGPT要約処理（略）

                    # シートに通知
                    send_to_spreadsheet("Dropbox", f"新しいファイル: {path}")

        return "Processed", 200

    except Exception as e:
        print(f"❌ エラー: {e}")
        abort(500)

if __name__ == "__main__":
    app.run(port=10000)