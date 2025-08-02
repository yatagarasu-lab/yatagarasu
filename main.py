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


# === Dropbox Webhook エンドポイント ===
@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return challenge, 200
    elif request.method == "POST":
        print("📦 Dropbox Webhook POST 受信しました")
        send_line_message("📦 Dropbox にファイルが追加または変更されました")
        return "", 200


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

@app.route("/line-webhook", methods=["POST"])
def line_webhook():
    payload = request.json
    try:
        events = payload.get("events", [])
        for event in events:
            if event.get("type") == "message" and event["message"].get("type") == "text":
                user_message = event["message"]["text"]
                reply_token = event["replyToken"]
                reply_to_line(reply_token, "ありがとうございます")
    except Exception as e:
        print(f"❌ LINE Webhook エラー: {e}")
    return "OK", 200

def reply_to_line(reply_token, message):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=data)


# === GAS連携（仮） ===
@app.route("/run-gas", methods=["POST"])
def run_gas():
    return jsonify({"status": "GAS call triggered (仮)"})


# === テスト用（Renderの稼働チェック） ===
@app.route("/", methods=["GET"])
def home():
    return "✅ AI統合サーバー稼働中"


# === 起動 ===
if __name__ == "__main__":
    app.run(debug=True)