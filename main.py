import os
import io
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage
from dotenv import load_dotenv
from dropbox import Dropbox

# 外部モジュール（強化版ロジック）
from analyzer import analyze_file
from notifier import build_summary_message

# .envから読み込み
load_dotenv()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# LINEとFlask初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
app = Flask(__name__)

# Dropbox接続
def get_dropbox_client():
    return Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )

dbx = get_dropbox_client()

# Webhookルート
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Webhook error: {e}")
        abort(400)

    return "OK"

# LINE画像受信イベント
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    content = line_bot_api.get_message_content(message_id)
    image_data = io.BytesIO(content.content)

    # ファイル保存先
    filename = f"{event.timestamp}.jpg"
    dropbox_path = f"/Apps/slot-data-analyzer/{filename}"

    # Dropboxアップロード
    image_data.seek(0)
    dbx.files_upload(image_data.read(), dropbox_path)
    image_data.seek(0)

    # 解析処理（強化版）
    summary = analyze_file(filename, image_data)

    # 通知送信（まとめ）
    summary_text = build_summary_message([summary])
    line_bot_api.push_message(LINE_USER_ID, TextMessage(text=summary_text))

# LINEテキスト受信イベント（任意のあいさつ）
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text
    reply = "こんにちは！画像を送ってくれたら要約します。" if "こんにちは" in text else "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 起動
if __name__ == "__main__":
    app.run()