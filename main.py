import os
import hashlib
import dropbox
from flask import Flask, request, abort
from dotenv import load_dotenv

from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.models import PushMessageRequest
from linebot.v3.webhooks import MessageEvent
from linebot.v3.webhooks import TextMessageContent, ImageMessageContent

load_dotenv()

app = Flask(__name__)

# LINE設定
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
user_id = os.getenv("LINE_USER_ID")

handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(channel_access_token)

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# 重複判定用ハッシュ生成関数
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# Dropboxに保存＋重複ファイル削除処理
def save_to_dropbox(filename, content):
    full_path = f"{DROPBOX_FOLDER_PATH}/{filename}"
    dbx.files_upload(content, full_path, mode=dropbox.files.WriteMode("overwrite"))

    # 重複削除処理
    hash_map = {}
    files = dbx.files_list_folder(DROPBOX_FOLDER_PATH).entries
    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            _, ext = os.path.splitext(file.name)
            if ext.lower() not in [".jpg", ".jpeg", ".png", ".txt"]:
                continue
            path = f"{DROPBOX_FOLDER_PATH}/{file.name}"
            data = dbx.files_download(path)[1].content
            h = file_hash(data)
            if h in hash_map:
                dbx.files_delete_v2(path)
            else:
                hash_map[h] = path

# LINE Webhookエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# メッセージ受信処理
@handler.add(MessageEvent)
def handle_message(event):
    message = event.message

    if isinstance(message, TextMessageContent):
        filename = f"text_{event.timestamp}.txt"
        save_to_dropbox(filename, message.text.encode())

    elif isinstance(message, ImageMessageContent):
        message_content = line_bot_api.get_message_content(message.id)
        data = b"".join(chunk for chunk in message_content.iter_content())
        filename = f"image_{event.timestamp}.jpg"
        save_to_dropbox(filename, data)

    # LINEへ返信
    line_bot_api.push_message(
        PushMessageRequest(
            to=user_id,
            messages=[TextMessage(text="ありがとうございます")]
        )
    )

# Flaskアプリ起動
