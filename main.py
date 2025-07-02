from flask import Flask, request
import os
import dropbox
import requests
import hashlib
import hmac

app = Flask(__name__)

# 環境変数から設定を取得
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")  # webhook検証用
LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN")
TARGET_FOLDER_PATH = "/スロットデータ"  # Dropbox内の監視対象フォルダ

# Dropboxクライアントの初期化
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Dropbox webhook 検証用（GETリクエスト）
@app.route("/webhook", methods=["GET"])
def verify_webhook():
    challenge = request.args.get("challenge")
    return challenge, 200

# Dropbox webhook 通知処理（POSTリクエスト）
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    signature = request.headers.get("X-Dropbox-Signature")
    request_body = request.data

    # セキュリティ検証（署名の一致）
    if not verify_signature(DROPBOX_APP_SECRET, request_body, signature):
        return "Invalid signature", 403

    # 更新されたユーザーID一覧を取得（Dropboxの仕様）
    for account in request.json.get("list_folder", {}).get("accounts", []):
        process_dropbox_changes(account)

    return "", 200

def verify_signature(secret, request_body, signature):
    computed_signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=request_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_signature, signature)

def process_dropbox_changes(account_id):
    # アカウントのカーソルを取得
    result = dbx.files_list_folder(TARGET_FOLDER_PATH, recursive=False)

    for entry in result.entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            filename = entry.name
            file_path = entry.path_display
            file_url = f"https://www.dropbox.com/home{file_path}"

            # LINE通知を送信
            send_line_notify(f"新しいファイルが追加されました：\n{filename}\n{file_url}")

def send_line_notify(message):
    headers = {
        "Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"
    }
    data = {
        "message": message
    }
    requests.post("https://notify-api.line.me/api/notify", headers=headers, data=data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)