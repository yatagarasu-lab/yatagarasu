import os
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import dropbox
from dotenv import load_dotenv
from gpt_utils import analyze_and_store

load_dotenv()

app = Flask(__name__)

# LINE
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

# Dropbox
dbx = dropbox.Dropbox(os.environ["DROPBOX_ACCESS_TOKEN"])

@app.route("/", methods=["GET"])
def health_check():
    return "Bot is running."

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    text = event.message.text
    print(f"受信: {user_id} → テキスト: {text}")

    filename = f"{event.timestamp}_text.txt"
    folder = f"/Apps/slot-data-analyzer/{user_id}"
    path = f"{folder}/{filename}"

    dbx.files_upload(text.encode(), path)
    analyze_and_store(text, filename, folder)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    message_id = event.message.id
    print(f"受信: {user_id} → 画像: {message_id}")

    image_content = line_bot_api.get_message_content(message_id)
    image_data = image_content.content.read()

    filename = f"{event.timestamp}_image.jpg"
    folder = f"/Apps/slot-data-analyzer/{user_id}"
    path = f"{folder}/{filename}"

    dbx.files_upload(image_data, path)
    analyze_and_store(image_data, filename, folder, is_image=True)

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))