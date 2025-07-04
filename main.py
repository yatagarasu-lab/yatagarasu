from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import os
import dropbox
from gpt_utils import process_with_gpt, process_with_gpt_image
from dropbox_handler import upload_to_dropbox
from duplicate_cleaner import find_and_remove_duplicates

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
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
    filename = f"{user_id}_{event.timestamp}.txt"

    # Dropboxにアップロード
    upload_to_dropbox(text.encode(), f"/スロットデータ/{filename}")
    find_and_remove_duplicates("/スロットデータ")

    # GPTで処理
    _ = process_with_gpt(text)

    # LINEに返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id).content
    filename = f"{user_id}_{message_id}.jpg"

    # Dropboxにアップロード
    upload_to_dropbox(image_content, f"/スロットデータ/{filename}")
    find_and_remove_duplicates("/スロットデータ")

    # GPTで処理
    _ = process_with_gpt_image(image_content)

    # LINEに返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge"), 200
    return "OK", 200

@app.route("/", methods=["GET"])
def health_check():
    return "LINE-Dropbox GPT Bot is running", 200