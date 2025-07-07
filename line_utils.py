import os
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 環境変数からトークンとユーザーIDを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")  # Uで始まるID

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def notify_user(text):
    """
    指定したテキストをLINEのユーザーに送信します。
    """
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
        print(f"✅ LINE通知送信完了: {text}")
    except Exception as e:
        print(f"❌ LINE通知エラー: {e}")