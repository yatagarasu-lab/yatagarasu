import os
import requests
from flask import Flask, request, abort
from io import BytesIO

from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, ImageMessage, TextSendMessage
)

# Flaskアプリ初期化
app = Flask(__name__)

# 環境変数からLINEとDropboxの認証情報取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

# LINE API初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Webhookエンドポイント
@app.route("/linewebhook", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK", 200

# テキストメッセージ処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text
    filename = f"text_{event.timestamp}.txt"
    save_to_dropbox(filename, text.encode("utf-8"))

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

# 画像メッセージ処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = BytesIO(message_content.content)
    filename = f"image_{event.timestamp}.jpg"
    save_to_dropbox(filename, image_data.read())

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

# Dropbox保存用関数
def save_to_dropbox(filename, content):
    url = "https://content.dropboxapi.com/2/files/upload"
    headers = {
        "Authorization": f"Bearer {DROPBOX_ACCESS_TOKEN}",
        "Dropbox-API-Arg": str({
            "path": f"/Apps/slot-data-analyzer/{filename}",
            "mode": "add",
            "autorename": True,
            "mute": False
        }).replace("'", '"'),
        "Content-Type": "application/octet-stream"
    }
    response = requests.post(url, headers=headers, data=content)
    if not response.ok:
        print("Dropbox upload failed:", response.text)

# アプリ実行（Render用なので不要だが念のため）
if __name__ == "__main__":
    app.run()