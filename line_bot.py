from flask import Blueprint, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from utils.logger import log_event

line_bp = Blueprint("line_bp", __name__)

# 環境変数からLINEの設定を取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@line_bp.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    log_event("LINE Webhook Received:\n" + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        log_event("⚠️ Invalid signature")
        return "Invalid signature", 400

    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    log_event(f"User Message: {user_message}")

    # 応答メッセージを固定（将来ここにGPT応答を追加可能）
    reply_text = "ありがとうございます"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )