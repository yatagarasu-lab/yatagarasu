import os
import hashlib
from io import BytesIO
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import dropbox
import openai
from PIL import Image

app = Flask(__name__)

# 環境変数からキー取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_ID = os.getenv("LINE_USER_ID")

# LINE設定
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox & GPT設定
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

# 重複チェック用
file_hashes = set()

def generate_hash(content):
    return hashlib.sha256(content).hexdigest()

def is_duplicate(content_hash):
    if content_hash in file_hashes:
        return True
    file_hashes.add(content_hash)
    return False

def upload_to_dropbox(file_bytes, file_name):
    path = f"/Apps/slot-data-analyzer/{file_name}"
    dbx.files_upload(file_bytes, path, mode=dropbox.files.WriteMode.overwrite)
    return path

def analyze_with_gpt(file_bytes, is_image=True):
    try:
        if is_image:
            # 画像のbase64形式をGPT Visionに送る
            response = openai.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "user", "content": [
                        {"type": "text", "text": "この画像の内容を要約してください。"},
                        {"type": "image_url", "image_url": {
                            "url": "data:image/jpeg;base64," + file_bytes.encode("base64").decode()
                        }}
                    ]}
                ],
                max_tokens=300
            )
        else:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": file_bytes}],
                max_tokens=300
            )
        return response.choices[0].message.content
    except Exception as e:
        return f"GPT解析エラー: {str(e)}"

# 通知済み画像のID（まとめ通知のため）
notified_ids = set()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id

    if message_id in notified_ids:
        return  # すでに通知済み

    notified_ids.add(message_id)

    # 画像取得
    message_content = line_bot_api.get_message_content(message_id)
    image_data = BytesIO(message_content.content)
    content = image_data.read()
    hash_val = generate_hash(content)

    if is_duplicate(hash_val):
        return  # 重複なら何もしない

    # Dropbox保存
    file_name = f"{message_id}.jpg"
    upload_to_dropbox(content, file_name)

    # GPT解析（コメントアウトで無効化可能）
    summary = analyze_with_gpt(content, is_image=True)

    # 通知（1通）
    line_bot_api.push_message(USER_ID, TextMessage(text="画像をDropboxに保存しました。ありがとうございます"))
    if summary:
        line_bot_api.push_message(USER_ID, TextMessage(text="要約: " + summary[:300]))

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text
    if len(text) < 10:
        line_bot_api.reply_message(event.reply_token, TextMessage(text="ありがとうございます"))
        return

    # 重複チェック
    hash_val = generate_hash(text.encode())
    if is_duplicate(hash_val):
        return

    # Dropbox保存
    file_name = f"{event.message.id}.txt"
    upload_to_dropbox(text.encode(), file_name)

    # GPT解析（要約）
    summary = analyze_with_gpt(text, is_image=False)
    line_bot_api.push_message(USER_ID, TextMessage(text="テキストをDropboxに保存しました。ありがとうございます"))
    if summary:
        line_bot_api.push_message(USER_ID, TextMessage(text="要約: " + summary[:300]))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)