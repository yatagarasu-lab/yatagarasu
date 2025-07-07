import os
import hashlib
import dropbox
import openai
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from dotenv import load_dotenv

load_dotenv()

# 環境変数の読み込み
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# OpenAI初期化
openai.api_key = OPENAI_API_KEY

# LINE API初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Flask初期化
app = Flask(__name__)

# Dropboxアクセストークン取得
def get_dbx():
    oauth_flow = dropbox.DropboxOAuth2FlowNoRedirect(DROPBOX_APP_KEY, consumer_secret=DROPBOX_APP_SECRET)
    dbx = dropbox.Dropbox(oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
                          app_key=DROPBOX_APP_KEY,
                          app_secret=DROPBOX_APP_SECRET)
    return dbx

def save_to_dropbox(file_content, filename):
    dbx = get_dbx()
    path = f"/Apps/slot-data-analyzer/{filename}"
    dbx.files_upload(file_content, path, mode=dropbox.files.WriteMode.overwrite)
    return path

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def is_duplicate(content, dbx):
    hash_value = file_hash(content)
    files = dbx.files_list_folder("/Apps/slot-data-analyzer").entries
    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            _, res = dbx.files_download(file.path_lower)
            existing_content = res.content
            if file_hash(existing_content) == hash_value:
                return True
    return False

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
def handle_text_message(event):
    text = event.message.text
    filename = f"text_{event.timestamp}.txt"
    save_to_dropbox(text.encode("utf-8"), filename)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    content = line_bot_api.get_message_content(event.message.id)
    file_data = content.content
    filename = f"image_{event.timestamp}.jpg"
    save_to_dropbox(file_data, filename)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

@app.route("/dropbox-webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge")
    elif request.method == "POST":
        process_dropbox_files()
        send_line_message("ありがとうございます")
        return "", 200

def process_dropbox_files():
    dbx = get_dbx()
    entries = dbx.files_list_folder("/Apps/slot-data-analyzer").entries
    seen_hashes = set()
    for file in entries:
        if isinstance(file, dropbox.files.FileMetadata):
            _, res = dbx.files_download(file.path_lower)
            content = res.content
            hash_val = file_hash(content)
            if hash_val in seen_hashes:
                dbx.files_delete_v2(file.path_lower)
            else:
                seen_hashes.add(hash_val)
                summary = summarize_content(content.decode("utf-8", errors="ignore"))
                print(f"{file.name} の要約: {summary}")

def summarize_content(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "以下を要約してください。"}, {"role": "user", "content": text}],
            max_tokens=300
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print("要約エラー:", e)
        return "要約できませんでした"

def send_line_message(message):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
    except Exception as e:
        print("LINE送信エラー:", e)

if __name__ == "__main__":
    app.run()