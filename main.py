from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage
import os
import tempfile
import dropbox
import hashlib

from gpt_logic import summarize_file
from dropbox_utils import upload_to_dropbox, list_files, download_file, file_hash

app = Flask(__name__)

# LINE Messaging API
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox API
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# 保存先パス
DATA_FOLDER = "/Apps/slot-data-analyzer"

@app.route("/")
def index():
    return "LINE-GPT-DROPBOX連携BOT"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Webhookエラー: {e}")
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text

    # 返信は全て固定
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text="ありがとうございます"))

    # GPTとのやりとりも保存
    filename = f"{event.timestamp}_user.txt"
    upload_to_dropbox(DATA_FOLDER + "/会話ログ/" + filename, text.encode())

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)

    with tempfile.NamedTemporaryFile(delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)

    filename = f"{event.timestamp}.jpg"

    # Dropboxにアップロード
    dropbox_path = DATA_FOLDER + "/画像/" + filename
    upload_to_dropbox(dropbox_path, open(tf.name, "rb").read())

    # GPT解析
    summary = summarize_file(open(tf.name, "rb").read(), filename)

    # 要約も保存
    summary_path = DATA_FOLDER + "/要約/" + filename.replace(".jpg", ".txt")
    upload_to_dropbox(summary_path, summary.encode())

    # LINEへ通知
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text="画像を受信し、解析・保存しました"))

# 重複検出タスク（定期または手動）
@app.route("/check_duplicates")
def check_duplicates():
    files = list_files(DATA_FOLDER)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

    return "重複チェック完了"

if __name__ == "__main__":
    app.run()