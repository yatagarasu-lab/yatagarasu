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

# ✅ Full Dropbox構成用のファイルパス（先頭スラッシュ必須）
DROPBOX_PATH = "/gpt_log.txt"

# 🔄 アクセストークンを取得
def get_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET,
    }
    res = requests.post(url, headers=headers, data=data)
    return res.json()["access_token"]

# ✅ Dropboxに追記保存
def append_to_dropbox(text):
    access_token = get_access_token()
    dbx = dropbox.Dropbox(access_token)

    # 既存ファイルを取得（存在しない場合は空文字）
    try:
        _, res = dbx.files_download(DROPBOX_PATH)
        existing = res.content.decode("utf-8")
    except dropbox.exceptions.ApiError:
        existing = ""

    # 新しいログを追加してアップロード
    new_log = existing + f"{datetime.now().isoformat()} - {text}\n"
    dbx.files_upload(new_log.encode("utf-8"), DROPBOX_PATH, mode=dropbox.files.WriteMode.overwrite)

# ✅ Dropboxから内容を読み取り
def read_from_dropbox():
    access_token = get_access_token()
    dbx = dropbox.Dropbox(access_token)

    try:
        _, res = dbx.files_download(DROPBOX_PATH)
        return res.content.decode("utf-8")
    except dropbox.exceptions.ApiError as e:
        return f"読み込みエラー: {e}"

# ✅ LINEやGPTから送信されたメッセージを保存
@app.route("/gpt", methods=["POST"])
def handle_message():
    data = request.get_json()
    message = data.get("message", "")
    append_to_dropbox(message)
    return jsonify({"status": "saved"}), 200

# ✅ Dropboxのログを取得（読み取り確認用）
@app.route("/logs", methods=["GET"])
def get_logs():
    content = read_from_dropbox()
    return content, 200

# ✅ Dropbox Webhook受信用（デバッグログ確認などに）
@app.route("/dropbox_webhook", methods=["POST", "GET"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge", "")
    elif request.method == "POST":
        print("🔔 Dropbox webhook triggered!")
        return "OK", 200

# ✅ 動作確認用のルート
@app.route("/", methods=["GET"])
def home():
    return "Yatagarasu BOT is running", 200