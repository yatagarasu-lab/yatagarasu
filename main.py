# main.py

import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage
)
from handle_text_message import handle_text_message
from handle_image_message import handle_image_message

app = Flask(__name__)

# LINE APIキーとシークレット
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# テキストメッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    handle_text_message(event, line_bot_api)

# 画像メッセージ受信時の処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    handle_image_message(event, line_bot_api)

if __name__ == "__main__":
    app.run()