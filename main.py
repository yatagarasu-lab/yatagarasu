from flask import Flask, request, jsonify
import dropbox
import os
import hashlib
from datetime import datetime
import requests

app = Flask(__name__)

# ✅ Dropbox環境変数
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

# ✅ Full Dropbox構成用のパス
FOLDER_PATH = "/slot-data-analyzer"
FILE_PATH = f"{FOLDER_PATH}/gpt_log.txt"

# 🔁 アクセストークンをリフレッシュで取得
def get_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET
    }
    res = requests.post(url, headers=headers, data=data)
    return res.json()["access_token"]

# 📁 フォルダがなければ作成
def ensure_folder_exists(dbx, folder_path):
    try:
        dbx.files_get_metadata(folder_path)
    except dropbox.exceptions.ApiError:
        dbx.files_create_folder_v2(folder_path)

# 📥 Dropboxにテキストを追記保存
def upload_to_dropbox(content):
    access_token = get_access_token()
    dbx = dropbox.Dropbox(oauth2_access_token=access_token)

    # フォルダ確認
    ensure_folder_exists(dbx, FOLDER_PATH)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {content}\n".encode("utf-8")

    try:
        metadata, res = dbx.files_download(FILE_PATH)
        existing = res.content + line
    except dropbox.exceptions.ApiError:
        existing = line

    dbx.files_upload(existing, FILE_PATH, mode=dropbox.files.WriteMode.overwrite)

# 📤 Dropboxからログを取得
def read_from_dropbox():
    access_token = get_access_token()
    dbx = dropbox.Dropbox(oauth2_access_token=access_token)

    try:
        metadata, res = dbx.files_download(FILE_PATH)
        return res.content.decode("utf-8")
    except dropbox.exceptions.ApiError:
        return "まだ記録がありません。"

# ✅ GPTからのログを保存
@app.route("/gpt", methods=["POST"])
def gpt_log():
    data = request.json
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "messageが空です"}), 400

    upload_to_dropbox(message)
    return jsonify({"status": "保存完了", "message": message})

# ✅ ログを表示
@app.route("/logs", methods=["GET"])
def get_logs():
    content = read_from_dropbox()
    return f"<pre>{content}</pre>"

# ✅ Dropbox Webhook受信エンドポイント
@app.route("/dropbox_webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge", "")
    if request.method == "POST":
        print("📩 Dropbox webhook通知受信:", request.get_json())
        return "", 200

# ✅ 起動確認用
@app.route("/", methods=["GET"])
def index():
    return "📦 GPT Dropbox Logger Running (Full Dropbox Mode)"

# 🔄 起動
if __name__ == "__main__":
    app.run(debug=True)