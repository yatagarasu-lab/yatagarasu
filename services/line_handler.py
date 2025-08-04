# services/line_handler.py

import os
from flask import request
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise Exception("LINEの環境変数が不足しています")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

def handle_line_request():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            user_message = event.message.text
            reply_token = event.reply_token
            line_bot_api.reply_message(reply_token, TextSendMessage(text="ありがとうございます"))

    return "OK", 200

def push_message_to_user(user_id, message):
    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=message))
    except Exception as e:
        print(f"[LINE] Pushメッセージ送信エラー: {e}")
