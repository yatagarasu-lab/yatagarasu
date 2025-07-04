import os
import hashlib
import dropbox
import openai
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from io import BytesIO

# 環境変数から設定を読み込み
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_ID = os.getenv("USER_ID")  # LINEのユーザーID

# 各種初期化
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

# 重複チェック用
hash_map = {}

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def upload_to_dropbox(content, filename):
    path = f"/Apps/slot-data-analyzer/{filename}"
    hash_val = file_hash(content)
    if hash_val in hash_map:
        print(f"❌ 重複ファイル（スキップ）: {filename}")
        return False
    else:
        dbx.files_upload(content, path, mode=dropbox.files.WriteMode.overwrite)
        hash_map[hash_val] = filename
        print(f"✅ Dropbox保存完了: {filename}")
        return True

def gpt_summarize(content):
    try:
        result = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "以下の内容を要約してください"},
                {"role": "user", "content": content.decode("utf-8", errors="ignore")}
            ]
        )
        return result.choices[0].message.content.strip()
    except Exception as e:
        print(f"GPT要約失敗: {e}")
        return None

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    print("📥 LINEからのWebhook受信:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    if event.source.user_id != USER_ID:
        return
    text = event.message.text.encode("utf-8")
    filename = f"text_{event.timestamp}.txt"
    if upload_to_dropbox(text, filename):
        summary = gpt_summarize(text)
        print("📝 要約:", summary)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    if event.source.user_id != USER_ID:
        return
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = BytesIO(message_content.content)
    filename = f"image_{event.timestamp}.jpg"
    if upload_to_dropbox(image_data.read(), filename):
        print("🖼️ 画像をDropboxに保存しました")
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

@app.route("/", methods=["GET"])
def index():
    return "サービス稼働中"