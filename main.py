from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import dropbox
import hashlib
import os
import base64

app = Flask(__name__)

# LINE設定
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.environ.get("LINE_USER_ID")  # Push通知先

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

# ハッシュで重複判定
def file_hash(content):
    return hashlib.md5(content).hexdigest()

def upload_to_dropbox(file_content, filename):
    path = f"{DROPBOX_FOLDER}/{filename}"
    dbx.files_upload(file_content, path, mode=dropbox.files.WriteMode.overwrite)
    return path

def is_duplicate(content):
    existing_files = dbx.files_list_folder(DROPBOX_FOLDER).entries
    content_hash = file_hash(content)
    for entry in existing_files:
        metadata, res = dbx.files_download(entry.path_display)
        existing_hash = file_hash(res.content)
        if existing_hash == content_hash:
            return True
    return False

# ============================
# ✅ LINE Webhookエンドポイント
# ============================
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# ============================
# ✅ LINEイベント処理
# ============================
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text.encode("utf-8")
    filename = f"text_{event.timestamp}.txt"
    if not is_duplicate(text):
        upload_to_dropbox(text, filename)
        line_bot_api.push_message(USER_ID, TextSendMessage(text="テキストをDropboxに保存しました"))
    else:
        line_bot_api.push_message(USER_ID, TextSendMessage(text="同じテキストが既に存在しています"))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    content = b"".join(chunk for chunk in message_content.iter_content())
    filename = f"image_{event.timestamp}.jpg"
    if not is_duplicate(content):
        upload_to_dropbox(content, filename)
        line_bot_api.push_message(USER_ID, TextSendMessage(text="画像をDropboxに保存しました"))
    else:
        line_bot_api.push_message(USER_ID, TextSendMessage(text="同じ画像が既に存在しています"))

# ============================
# ✅ ルート確認用（オプション）
# ============================
@app.route("/", methods=["GET"])
def index():
    return "LINE BOT 起動中 - /callback を使用してください"

# ============================
# ✅ アプリ起動
# ============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))