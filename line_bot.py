from flask import Blueprint, request
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import datetime
import pytz

# LINE設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")  # Push送信用

line_bp = Blueprint("line_bot", __name__)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

# 夜間判定（22:00～翌6:00のみ許可）
def is_nighttime():
    tz = pytz.timezone('Asia/Tokyo')
    now = datetime.datetime.now(tz).time()
    return now >= datetime.time(22, 0) or now <= datetime.time(6, 0)

# LINE Webhook受信処理（応答専用）
@line_bp.route("/line", methods=["POST"])
def callback():
    if not is_nighttime():
        return "昼間のため応答制限中", 200

    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="ありがとうございます")
            )

    return "OK", 200

# LINE Push通知用
def push_line_message(message):
    if is_nighttime():  # 夜間のみ送信許可
        line_bot_api.push_message(USER_ID, TextSendMessage(text=message))
