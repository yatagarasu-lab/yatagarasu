import os
from linebot import LineBotApi
from linebot.models import TextSendMessage

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

def send_line_message(message):
    line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
    line_bot_api.push_message(USER_ID, TextSendMessage(text=message))