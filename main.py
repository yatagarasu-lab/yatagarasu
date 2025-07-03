from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage
import dropbox
import os
import hashlib
import openai

app = Flask(__name__)

# 環境変数からトークン取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

FOLDER_PATH = "/Apps/slot-data-analyzer"

def file_exists(folder_path):
    try:
        res = dbx.files_list_folder(folder_path)
        return res.entries
    except:
        return []

def upload_file(file_name, file_data):
    dbx.files_upload(file_data, f"{FOLDER_PATH}/{file_name}", mode=dropbox.files.WriteMode.overwrite)

def get_file_hash(file_path):
    _, res = dbx.files_download(file_path)
    return res.content

def analyze_file_content(file_data):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "画像の内容を要約し、重複がないか確認して分析してください。"},
                {"role": "user", "content": "画像が届きました。内容をチェックしてください。"}
            ]
        )
        return response.choices[0].message["content"]
    except:
        return "ファイルを受け取りました（要約機能は未使用です）"

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    message_id = event.message.id
    file_name = f"{user_id}_{message_id}.jpg"

    image_content = line_bot_api.get_message_content(message_id)
    file_data = image_content.content

    # ハッシュ生成で重複チェック
    new_hash = hashlib.sha256(file_data).hexdigest()
    entries = file_exists(FOLDER_PATH)
    for entry in entries:
        if not entry.name.endswith(".jpg"):
            continue
        existing_data = get_file_hash(f"{FOLDER_PATH}/{entry.name}")
        if new_hash == hashlib.sha256(existing_data).hexdigest():
            reply = "重複ファイルのため保存されませんでした。"
            break
    else:
        upload_file(file_name, file_data)
        reply = "画像をDropboxに保存しました。\n\n" + analyze_file_content(file_data)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"