# line_push.py

import os
from linebot import LineBotApi
from linebot.models import TextSendMessage

def send_line_message(text):
    if os.getenv("LINE_PUSH_ENABLED", "false").lower() != "true":
        print("LINE通知は無効化されています。")
        return

    access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("LINE_USER_ID")

    if not access_token or not user_id:
        print("LINE通知に必要な情報が不足しています。")
        return

    line_bot_api = LineBotApi(access_token)
    try:
        line_bot_api.push_message(user_id, TextSendMessage(text=text))
        print("LINEに通知を送信しました。")
    except Exception as e:
        print(f"LINE通知エラー: {e}")
