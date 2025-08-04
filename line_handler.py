# line_handler.py

from flask import request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

# 環境変数からトークン・シークレット取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_CHANNEL_SECRET:
    raise ValueError("LINEのトークンまたはシークレットが設定されていません。")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def handle_line_webhook():
    signature = request.headers.get("X-Line-Signature")

    body = request.get_data(as_text=True)
    print("Request body:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    print(f"受信メッセージ: {user_text}")

    # 応答メッセージ（ここは後でGPTと連携可）
    reply_text = "ありがとうございます"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )