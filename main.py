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

load_dotenv()

# 環境変数読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI初期化
openai.api_key = OPENAI_API_KEY

# LINE初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Flask初期化
app = Flask(__name__)

# Dropbox認証（リフレッシュトークン方式）
def get_dropbox_client():
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox
    from dropbox.oauth import OAuth2AccessToken
    from dropbox import DropboxOAuth2Flow

    from dropbox import Dropbox, DropboxOAuth2FlowNoRedirect
    from dropbox.oauth import OAuth2AccessToken, OAuth2Flow, OAuth2Session

    oauth_result = dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )
    return oauth_result

dbx = get_dropbox_client()

# ファイル保存先
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

# 画像受信処理
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

# メッセージ受信イベント
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_id = event.message.id
    content = line_bot_api.get_message_content(message_id)

    image_data = io.BytesIO(content.content)
    image = Image.open(image_data)

    # OCR解析（必要に応じて省略可）
    text = pytesseract.image_to_string(image, lang="jpn")

    # GPT要約
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "次の日本語テキストを要約してください。"},
            {"role": "user", "content": text}
        ]
    )
    summary = response.choices[0].message["content"]

    # Dropboxに保存
    filename = f"{event.timestamp}.jpg"
    path = f"{DROPBOX_FOLDER}/{filename}"
    image_data.seek(0)
    dbx.files_upload(image_data.read(), path)

    # LINEに通知
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=f"画像の要約:\n{summary}")
    )

# LINEでテキストメッセージも処理（任意）
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    if "こんにちは" in text:
        reply = "こんにちは！画像を送ってくれたら要約します。"
    else:
        reply = "ありがとうございます"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

# アプリ起動
if __name__ == "__main__":
    app.run()