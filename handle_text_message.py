# handle_text_message.py
from linebot.models import TextSendMessage

def handle_text_message(event, line_bot_api):
    """受け取ったテキストメッセージに返信する関数"""
    reply_text = "ありがとうございます"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )