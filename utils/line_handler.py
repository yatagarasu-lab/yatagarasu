# utils/line_handler.py

import os
import tempfile
from linebot.models import TextSendMessage
from services.gpt_summarizer import summarize_text
from services.dropbox_uploader import upload_to_dropbox
from services.image_handler import handle_image_file

# テキストメッセージ処理
def handle_text_message(event, line_bot_api):
    user_text = event.message.text

    # GPTで要約（オプション）
    summary = summarize_text(user_text)
    
    # Dropboxに保存
    filename = f"text_{event.timestamp}.txt"
    with tempfile.NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8") as tmp:
        tmp.write(user_text)
        tmp_path = tmp.name
    upload_to_dropbox(tmp_path, f"/text/{filename}")

    # LINEに返信（要約 or ありがとう）
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます。")
    )

# 画像メッセージ処理
def handle_image_message(event, line_bot_api):
    message_id = event.message.id
    image_path = f"/tmp/{message_id}.jpg"

    # 画像を一時保存
    message_content = line_bot_api.get_message_content(message_id)
    with open(image_path, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

    # Dropboxにアップロード
    dropbox_path = f"/images/{message_id}.jpg"
    upload_to_dropbox(image_path, dropbox_path)

    # GPT画像処理（例：要約や内容チェック）
    result_text = handle_image_file(image_path)

    # LINE返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます。")
    )
