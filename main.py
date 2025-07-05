import os
import hashlib
import time
import json
from flask import Flask, request
import dropbox
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage

app = Flask(__name__)

# DropboxとLINEの環境変数
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# ファイル重複判定用ハッシュマップと通知タイミング制御
file_hash_map = {}
last_notified_time = 0
notify_interval = 30  # 秒（30秒間は1通だけ通知）

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def upload_and_check(file_path, content):
    global file_hash_map

    hash_val = file_hash(content)
    if hash_val in file_hash_map:
        print(f"重複検出: {file_path}")
        return False
    file_hash_map[hash_val] = file_path
    dbx.files_upload(content, f"/Apps/slot-data-analyzer/{file_path}", mode=dropbox.files.WriteMode.overwrite)
    return True

def send_line_message(message):
    global last_notified_time
    now = time.time()
    if now - last_notified_time > notify_interval:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
        last_notified_time = now
    else:
        print("通知は省略（まとめて1通）")

@app.route("/callback", methods=["POST"])
def callback():
    data = request.get_json()
    print("受信データ:", json.dumps(data, indent=2, ensure_ascii=False))

    for event in data.get("events", []):
        msg_type = event["message"]["type"]
        message_id = event["message"]["id"]

        if msg_type == "image":
            # 画像の取得と保存
            content = line_bot_api.get_message_content(message_id).content
            file_name = f"{message_id}.jpg"
            if upload_and_check(file_name, content):
                send_line_message("画像を Dropbox に保存しました。\nありがとうございます")
        elif msg_type == "text":
            text = event["message"]["text"]
            file_name = f"{message_id}.txt"
            if upload_and_check(file_name, text.encode()):
                send_line_message("テキストを Dropbox に保存しました。\nありがとうございます")

    return "OK", 200

@app.route("/", methods=["GET"])
def index():
    return "動作中"

if __name__ == "__main__":
    app.run()