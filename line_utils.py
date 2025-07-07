import os
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 環境変数からLINEトークン取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")  # 送信先ユーザーID
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Push通知を送る
def push_message(text, user_id=LINE_USER_ID):
    try:
        message = TextSendMessage(text=text)
        line_bot_api.push_message(user_id, messages=[message])
        print(f"✅ LINEに送信: {text}")
    except Exception as e:
        print(f"❌ LINE送信失敗: {e}")