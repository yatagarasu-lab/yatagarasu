import os
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 環境変数から取得（Render で設定済み想定）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")  # 固定ユーザー用（例: Uxxxxxx）

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def push_line_message(text: str):
    try:
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=text)
        )
        print(f"LINE送信成功: {text[:50]}...")
    except Exception as e:
        print(f"LINE送信失敗: {e}")