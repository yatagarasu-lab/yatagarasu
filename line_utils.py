from linebot import LineBotApi
from linebot.models import TextSendMessage
import os

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def send_custom_line_notification(user_id, summary, path):
    """
    GPTからの要約とDropboxの保存先を含むカスタム通知をLINEに送信
    """
    try:
        tag_part = summary.split("【タグ】")[1].strip()
        summary_part = summary.split("【タグ】")[0].replace("【要約】", "").strip()
    except:
        tag_part = "タグなし"
        summary_part = summary.strip()

    message = (
        "📩 新しいスロット情報を受信しました！\n\n"
        f"📝 要約：\n{summary_part}\n\n"
        f"🏷 タグ：\n{tag_part}\n\n"
        f"📁 保存先：{path}"
    )
    line_bot_api.push_message(user_id, TextSendMessage(text=message))