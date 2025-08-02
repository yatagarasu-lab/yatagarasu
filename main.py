from flask import Flask, request, jsonify
import requests
import json
import os
import time
import base64

app = Flask(__name__)

# === Dropbox API（リフレッシュトークン方式） ===
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

def get_dropbox_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

@app.route("/dropbox-files", methods=["GET"])
def list_dropbox_files():
    token = get_dropbox_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        "https://api.dropboxapi.com/2/files/list_folder",
        headers=headers,
        json={"path": ""}
    )
    return jsonify(response.json())

# === LINE API ===
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def send_line_message(message):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)

@app.route("/line-hook", methods=["POST"])
def line_webhook():
    payload = request.json
    try:
        text = payload["events"][0]["message"]["text"]
        reply_token = payload["events"][0]["replyToken"]
        reply(text, reply_token)
    except Exception as e:
        print(f"Error in webhook: {e}")
    return "ok"

def reply(text, reply_token):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": "ありがとうございます"}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=data)

# === GAS 連携（将来の自動トリガー実装用） ===
@app.route("/run-gas", methods=["POST"])
def run_gas():
    # 仮設：ここに GAS API エンドポイント or Apps Script Web API を呼ぶコードを入れる
    return jsonify({"status": "GAS call triggered (仮)"})

# === テスト用 ===
@app.route("/", methods=["GET"])
def home():
    return "✅ AI統合サーバー稼働中"

if __name__ == "__main__":
    app.run(debug=True)