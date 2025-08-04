from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, FileMessage
from services.line_handler import save_line_content_to_dropbox

import os

app = Flask(__name__)

# 環境変数からLINE設定を取得
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# LINE Webhookエンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Webhook Error: {e}")
        return "Error", 400

    return "OK", 200

# テキストメッセージ（任意で応答可能）
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

# 画像メッセージを受信 → Dropbox保存
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    save_line_content_to_dropbox(event)

# ファイルメッセージを受信 → Dropbox保存
@handler.add(MessageEvent, message=FileMessage)
def handle_file_message(event):
    save_line_content_to_dropbox(event)

# 動作テスト用のルート
@app.route("/", methods=["GET"])
def root():
    return "LINE Bot Webhook is running!"