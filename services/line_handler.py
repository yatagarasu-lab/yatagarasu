import os
from flask import request, Response
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 環境変数からLINEチャネル情報を取得
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

def handle_line_webhook(req):
    signature = req.headers.get("X-Line-Signature", "")
    body = req.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return Response("Invalid signature", status=403)

    return Response("OK", status=200)

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    reply = "ありがとうございます"  # 固定返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )