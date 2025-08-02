from flask import Flask, request, jsonify
import dropbox
import os
import hashlib
from datetime import datetime

app = Flask(__name__)

# Dropboxアクセストークンなど環境変数から取得
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
DROPBOX_PATH = "/Apps/slot-data-analyzer/gpt_log.txt"

# 🔁 Dropboxアクセストークン取得
def get_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET
    }
    import requests
    res = requests.post(url, headers=headers, data=data)
    return res.json()["access_token"]

# 📥 Dropboxにファイル保存
def upload_to_dropbox(content):
    access_token = get_access_token()
    dbx = dropbox.Dropbox(oauth2_access_token=access_token)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {content}\n".encode("utf-8")

    try:
        metadata, res = dbx.files_download(DROPBOX_PATH)
        existing = res.content + line
    except dropbox.exceptions.ApiError:
        existing = line

    dbx.files_upload(existing, DROPBOX_PATH, mode=dropbox.files.WriteMode.overwrite)

# 📤 Dropboxから読み込み
def read_from_dropbox():
    access_token = get_access_token()
    dbx = dropbox.Dropbox(oauth2_access_token=access_token)

    try:
        metadata, res = dbx.files_download(DROPBOX_PATH)
        return res.content.decode("utf-8")
    except dropbox.exceptions.ApiError:
        return "まだ記録がありません。"

# 🧠 GPTメッセージ受信 → Dropboxに記録
@app.route("/gpt", methods=["POST"])
def gpt_log():
    data = request.json
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "messageが空です"}), 400

    upload_to_dropbox(message)
    return jsonify({"status": "保存完了", "message": message})

# 📚 ログ確認
@app.route("/logs", methods=["GET"])
def get_logs():
    content = read_from_dropbox()
    return f"<pre>{content}</pre>"

# 🪝 Dropbox Webhook
@app.route("/dropbox_webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge", "")
    if request.method == "POST":
        # 今は通知を受け取るだけ
        print("Dropbox webhook通知受信:", request.get_json())
        return "", 200

# 🔓 簡易トップ確認
@app.route("/", methods=["GET"])
def index():
    return "📦 GPT Dropbox Logger Running"

if __name__ == "__main__":
    app.run(debug=True)