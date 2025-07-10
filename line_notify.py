import os
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 環境変数からLINE設定を取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def send_line_message(message: str):
    try:
        if not LINE_USER_ID:
            raise ValueError("LINE_USER_ID が未設定です。")
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
    except Exception as e:
        print(f"LINE通知エラー: {e}")