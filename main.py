from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import os

from dropbox_handler import upload_file, upload_text
from gpt_utils import process_with_gpt, process_with_gpt_image

app = Flask(__name__)

line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

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
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text
    filename = f"/スロットデータ/{user_id}_{event.timestamp}.txt"
    upload_text(filename, text)
    process_with_gpt(text)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id).content
    filename = f"/スロットデータ/{user_id}_{message_id}.jpg"
    upload_file(filename, image_content)
    process_with_gpt_image(image_content)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge", ""), 200
    return "OK", 200

@app.route("/", methods=["GET"])
def health_check():
    return "LINE-Dropbox GPT Bot is running", 200