import os
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 環境変数からLINEトークンとユーザーIDを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# LINE Bot APIの初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# 通知送信関数
def push_message(message):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
        print(f"✅ LINEに送信しました: {message}")
    except Exception as e:
        print(f"❌ LINE通知エラー: {e}")