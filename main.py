from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# === Dropbox API（リフレッシュトークン方式） ===
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

def get_dropbox_access_token():
    try:
        url = "https://api.dropbox.com/oauth2/token"
        data = {
            "grant_type": "refresh_token",
            "refresh_token": DROPBOX_REFRESH_TOKEN,
            "client_id": DROPBOX_CLIENT_ID,
            "client_secret": DROPBOX_CLIENT_SECRET
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        token = response.json().get("access_token")
        print("✅ Dropbox アクセストークン取得成功")
        return token
    except Exception as e:
        print(f"❌ Dropbox アクセストークン取得失敗: {e}")
        return None

@app.route("/dropbox-files", methods=["GET"])
def list_dropbox_files():
    token = get_dropbox_access_token()
    if not token:
        return jsonify({"error": "Dropbox access token error"}), 500
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        "https://api.dropboxapi.com/2/files/list_folder",
        headers=headers,
        json={"path": ""}
    )
    return jsonify(response.json())

# === 通知のスパム防止用 ===
last_notification_time = None

# === Dropbox Webhook エンドポイント ===
@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    global last_notification_time

    if request.method == "GET":
        challenge = request.args.get("challenge")
        print(f"✅ Dropbox webhook チャレンジ応答: {challenge}")
        return challenge, 200

    elif request.method == "POST":
        now = datetime.now()
        if last_notification_time and now - last_notification_time < timedelta(minutes=2):
            print("⏳ 通知スキップ（2分以内の連続）")
            return "", 200

        last_notification_time = now
        print("📦 Dropbox Webhook POST 受信しました → 通知送信")
        send_line_message("📦 Dropbox にファイルが追加または変更されました")
        return "", 200

# === LINE API ===
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def send_line_message(message):
    try:
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "to": LINE_USER_ID,
            "messages": [{"type": "text", "text": message}]
        }
        res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)
        res.raise_for_status()
        print("✅ LINE Push通知 成功")
    except Exception as e:
        print(f"❌ LINE通知失敗: {e}")

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
        print("✅ LINE Webhook 正常受信")
    except Exception as e:
        print(f"❌ LINE Webhook エラー: {e}")
    return "OK", 200

def reply_to_line(reply_token, message):
    try:
        headers = {
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        data = {
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": message}]
        }
        requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=data)
        print("✅ LINE返信 成功")
    except Exception as e:
        print(f"❌ LINE返信失敗: {e}")

# === GAS連携（仮） ===
@app.route("/run-gas", methods=["POST"])
def run_gas():
    print("✅ GAS起動（仮）")
    return jsonify({"status": "GAS call triggered (仮)"})


# === テスト用（Renderの稼働チェック） ===
@app.route("/", methods=["GET"])
def home():
    return "✅ AI統合サーバー稼働中"


# === 起動 ===
if __name__ == "__main__":
    app.run(debug=True)