import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Flask アプリ作成
app = Flask(__name__)

# 環境変数から読み込み（Renderに登録済みが前提）
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
GOOGLE_CLOUD_VISION_KEY = os.getenv("GOOGLE_CLOUD_VISION_KEY")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("USER_ID")

# LINE bot 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- Webhook エンドポイント ---
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# --- LINEメッセージ受信処理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply_text = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# --- Renderのヘルスチェック用 ---
@app.route("/")
def index():
    return "App is running", 200