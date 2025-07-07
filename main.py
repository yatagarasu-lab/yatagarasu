import os
import io
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from dotenv import load_dotenv
import dropbox
import openai
from PIL import Image
import pytesseract

# 環境変数読み込み
load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)

# Dropbox初期化
def get_dropbox_client():
    return dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )

dbx = get_dropbox_client()
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

# LINEのWebhookエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error: {e}")
        abort(400)
    return "OK"

# 画像受信イベント
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_id = event.message.id
    content = line_bot_api.get_message_content(message_id)
    image_data = io.BytesIO(content.content)

    # OCRでテキスト抽出
    image = Image.open(image_data)
    text = pytesseract.image_to_string(image, lang="jpn")

    # GPTで要約
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "次の日本語テキストを要約してください。"},
            {"role": "user", "content": text}
        ]
    )
    summary = response.choices[0].message["content"]

    # Dropbox保存
    filename = f"{event.timestamp}.jpg"
    image_data.seek(0)
    dbx.files_upload(image_data.read(), f"{DROPBOX_FOLDER}/{filename}")

    # LINEに要約を送信
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=f"画像の要約:\n{summary}")
    )

# テキストメッセージにも対応
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    reply = "こんにちは！画像を送ってくれたら要約します。" if "こんにちは" in event.message.text else "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# Flaskアプリ（Render用）
app = app  # ← gunicorn が使う