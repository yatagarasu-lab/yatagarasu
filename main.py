from flask import Flask, request, jsonify
import dropbox
import os
from datetime import datetime
import requests

app = Flask(__name__)

# ✅ Dropbox 環境変数（Renderなどで設定済みであること）
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

# ✅ Full Dropbox構成用（ルート直下）
DROPBOX_PATH = "/gpt_log.txt"

# 🔁 Dropbox アクセストークン取得（refresh_tokenから）
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

# 📥 Dropbox に内容を追記保存
def upload_to_dropbox(content):
    access_token = get_access_token()
    dbx = dropbox.Dropbox(oauth2_access_token=access_token)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {content}\n".encode("utf-8")

    try:
        metadata, res = dbx.files_download(DROPBOX_PATH)
        existing = res.content + line
    except dropbox.exceptions.ApiError:
        existing = line  # 初回ファイルがない場合

    dbx.files_upload(existing, DROPBOX_PATH, mode=dropbox.files.WriteMode.overwrite)

# 📤 Dropbox の内容を取得
def read_from_dropbox():
    access_token = get_access_token()
    dbx = dropbox.Dropbox(oauth2_access_token=access_token)

    try:
        metadata, res = dbx.files_download(DROPBOX_PATH)
        return res.content.decode("utf-8")
    except dropbox.exceptions.ApiError:
        return "まだ記録がありません。"

# ✅ GPTメッセージ受信 → Dropboxへ記録
@app.route("/gpt", methods=["POST"])
def gpt_log():
    data = request.json
    message = data.get("message", "")
    if not message:
        return jsonify({"error": "messageが空です"}), 400

    upload_to_dropbox(message)
    return jsonify({"status": "保存完了", "message": message})

# ✅ 記録されたログを表示
@app.route("/logs", methods=["GET"])
def get_logs():
    content = read_from_dropbox()
    return f"<pre>{content}</pre>"

# ✅ Dropbox Webhook エンドポイント
@app.route("/dropbox_webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge", "")
    if request.method == "POST":
        print("Dropbox webhook通知受信:", request.get_json())
        return "", 200

# ✅ 動作確認用トップページ
@app.route("/", methods=["GET"])
def index():
    return "📦 GPT Dropbox Logger Running"

# ✅ ローカル実行用（Renderでは不要）
if __name__ == "__main__":
    app.run(debug=True)