# services/line_notifier.py
import os
from linebot import LineBotApi, WebhookParser
from linebot.models import TextSendMessage

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def push_text_to_line(message: str):
    try:
        line_bot_api.push_message(
            USER_ID,
            TextSendMessage(text=message)
        )
        print("✅ LINE通知送信成功:", message)
    except Exception as e:
        print("❌ LINE通知送信エラー:", e)