import os
import tempfile
import hashlib
import dropbox
import openai
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage

# 環境変数の読み込み（Renderで設定済み）
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_USER_ID = os.getenv("USER_ID")

# 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

app = Flask(__name__)

# 重複ファイル検出用ハッシュ辞書
file_hash_map = {}

# ファイル保存先
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

def file_hash(data):
    return hashlib.sha256(data).hexdigest()

def upload_to_dropbox(file_data, filename):
    path = f"{DROPBOX_FOLDER}/{filename}"
    dbx.files_upload(file_data, path, mode=dropbox.files.WriteMode("overwrite"))
    return path

def is_duplicate(data):
    h = file_hash(data)
    if h in file_hash_map:
        return True
    file_hash_map[h] = True
    return False

def analyze_image_with_gpt(image_url):
    response = openai.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "この画像の内容を分析してください（スロットの設定やイベント傾向なども含めて）。"},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

def notify_line(text):
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))

@app.route("/", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)

    with tempfile.NamedTemporaryFile(delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tf_path = tf.name

    with open(tf_path, "rb") as f:
        data = f.read()

    if is_duplicate(data):
        notify_line("重複した画像です。処理をスキップします。")
        return

    filename = f"{message_id}.jpg"
    upload_to_dropbox(data, filename)

    # 一時リンクで画像URL取得
    shared_link_metadata = dbx.sharing_create_shared_link_with_settings(f"{DROPBOX_FOLDER}/{filename}")
    image_url = shared_link_metadata.url.replace("?dl=0", "?raw=1")

    notify_line("画像をDropboxに保存しました。解析を開始します…")

    try:
        result = analyze_image_with_gpt(image_url)
        notify_line(f"【画像解析結果】\n{result}")
    except Exception as e:
        notify_line(f"解析中にエラーが発生しました: {e}")

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    notify_line("ありがとうございます")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))