from flask import request, abort
from linebot import WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import os
import tempfile
from dropbox_handler import upload_file
from gpt_handler import analyze_text, analyze_image

handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# LINEからのWebhookを処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_text = event.message.text
    file_name = f"text_{event.timestamp}.txt"

    # Dropboxへ保存
    upload_file(file_name, user_text.encode("utf-8"))

    # GPTで解析
    result = analyze_text(user_text, file_name)

    # LINEへ返信（上限4,000文字に制限）
    event.reply_token and event.source.user_id and \
        request.environ.get("line_bot_api").push_message(
            event.source.user_id,
            TextSendMessage(text=result[:4000])
        )


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    line_bot_api = request.environ.get("line_bot_api")

    # 一時ファイルに保存
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        message_content = line_bot_api.get_message_content(event.message.id)
        for chunk in message_content.iter_content():
            tf.write(chunk)
        temp_file_path = tf.name

    # Dropboxへ保存
    file_name = f"image_{event.timestamp}.jpg"
    with open(temp_file_path, "rb") as f:
        upload_file(file_name, f.read())

    # GPTで解析
    with open(temp_file_path, "rb") as f:
        result = analyze_image(f.read(), file_name)

    # LINEへ返信（上限4,000文字）
    line_bot_api.push_message(
        event.source.user_id,
        TextSendMessage(text=result[:4000])
    )