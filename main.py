from flask import Flask, request, abort
import os
import json
import dropbox
import requests
import hashlib
import time
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox設定（リフレッシュ対応）
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_ACCESS_TOKEN = None  # 初期状態

def refresh_dropbox_token():
    global DROPBOX_ACCESS_TOKEN
    url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_APP_KEY,
        "client_secret": DROPBOX_APP_SECRET,
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        DROPBOX_ACCESS_TOKEN = response.json()["access_token"]
        print("✅ Dropboxトークンを更新しました。")
    else:
        print("❌ Dropboxトークンの更新に失敗しました。", response.text)

# 最初に1回トークン更新
refresh_dropbox_token()

@app.route("/", methods=["GET"])
def home():
    return "✅ Slot Data Analyzer Bot is running."

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # Dropboxのチャレンジ検証（GET）
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return challenge, 200

    # LINEからのPOST受信処理
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_message = event.message.text
    reply_text = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))