import os
import hashlib
import time
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, ImageMessage
import dropbox
import openai
from io import BytesIO

# 環境変数からキーを取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
DROPBOX_ACCESS_TOKEN = os.environ["DROPBOX_ACCESS_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

# 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

def save_to_dropbox(image_bytes):
    timestamp = str(int(time.time() * 1000))
    path = f"/Apps/slot-data-analyzer/{timestamp}.jpg"
    dbx.files_upload(image_bytes, path)
    print(f"画像保存完了：{path}")
    return path

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    time.sleep(2)  # Dropboxに反映されるまで待つ
    try:
        md, res = dbx.files_download(path)
        return res.content
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox APIエラー: {e}")
        return None

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        if content is None:
            continue
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # 重複を削除したい場合は以下を有効化
            # dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

def analyze_image_with_gpt(image_bytes):
    response = openai.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": "この画像の内容を要約してください"},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + image_bytes.encode('base64')}}
            ]}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Handle error: {e}")
    return "OK"

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = BytesIO()
    for chunk in message_content.iter_content():
        image_data.write(chunk)

    image_bytes = image_data.getvalue()
    path = save_to_dropbox(image_bytes)

    # 重複チェック
    find_duplicates()

    # LINE返信
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text="ありがとうございます"))

@app.route("/", methods=["GET"])
def home():
    return "OK"