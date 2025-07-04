import os
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import openai
import dropbox
from io import BytesIO
import requests

app = Flask(__name__)

# 環境変数の読み込み
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")  # 例: "U8da89a1a4e1689bbf7077dbdf0d47521"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# ファイルハッシュで重複チェック
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def is_duplicate(file_path, content_hash):
    try:
        files = dbx.files_list_folder(file_path).entries
        for file in files:
            md = dbx.files_get_metadata(file.path_lower)
            if hasattr(md, 'content_hash') and md.content_hash == content_hash:
                return True
    except Exception:
        pass
    return False

def upload_to_dropbox(file_bytes, file_name, folder="/Apps/slot-data-analyzer"):
    path = f"{folder}/{file_name}"
    file_hash_val = file_hash(file_bytes)
    if not is_duplicate(folder, file_hash_val):
        dbx.files_upload(file_bytes, path, mode=dropbox.files.WriteMode("add"))
        return path
    return None

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    file_name = f"text_{event.timestamp}.txt"
    upload_to_dropbox(text.encode(), file_name)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = BytesIO()
    for chunk in message_content.iter_content():
        image_data.write(chunk)
    image_data.seek(0)
    file_name = f"image_{event.timestamp}.jpg"
    uploaded_path = upload_to_dropbox(image_data.read(), file_name)
    image_data.seek(0)

    # GPT解析（オプション）
    analysis_result = "画像を受信しました。ありがとうございます。"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=analysis_result)
    )

# Render用
@app.route("/", methods=["GET"])
def home():
    return "Our service is live 🎉"

if __name__ == "__main__":
    app.run()