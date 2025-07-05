from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage

import os
from handle_text_message import handle_text_message
from analyze_and_notify import analyze_dropbox_updates

app = Flask(__name__)

# 環境変数からLINEアクセストークンとシークレットを取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise ValueError("環境変数にLINEのトークンが設定されていません。")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ルート確認用
@app.route("/", methods=["GET"])
def home():
    return "LINE-Dropbox-GPT Bot is running!"

# LINE Webhook受信用エンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")

    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# テキストメッセージイベントを処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    handle_text_message(event, line_bot_api)

# Dropbox Webhookエンドポイント
@app.route("/dropbox-webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        # Webhook認証のためのchallenge
        challenge = request.args.get("challenge")
        return challenge, 200
    elif request.method == "POST":
        # Dropbox更新が通知されたときに呼ばれる
        analyze_dropbox_updates()
        return "OK", 200