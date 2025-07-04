from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import dropbox
import os
import hashlib

app = Flask(__name__)

# LINE
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
LINE_USER_ID = os.environ.get("LINE_USER_ID")  # 固定ユーザーID

# Dropbox
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def list_files(folder_path):
    return dbx.files_list_folder(folder_path).entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def find_duplicates(folder_path=DROPBOX_FOLDER_PATH):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

# ✅ Dropbox Webhook エンドポイント
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge"), 200
    elif request.method == "POST":
        print("✅ Dropbox Webhook POST 受信")
        find_duplicates()
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text="Dropboxに新しいファイルが追加され、重複チェックが完了しました。")
        )
        return "OK", 200
    else:
        abort(400)

# ✅ LINE Webhook エンドポイント
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
def handle_message(event):
    text = event.message.text
    line_bot