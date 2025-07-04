from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage

from dropbox_handler import (
    upload_zip_to_dropbox,
    download_file
)
from gpt_handler import analyze_zip_content

import os
import tempfile
from datetime import datetime

app = Flask(__name__)

# 環境変数から各種トークンを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ---------- LINE Webhookエンドポイント ----------
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ---------- LINEメッセージ受信時の処理 ----------
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    filename = f"スロットデータ/テキスト_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    upload_zip_to_dropbox(filename, text.encode())

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="📄 テキストをDropboxに保存しました。")
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_image:
        for chunk in message_content.iter_content():
            temp_image.write(chunk)
        temp_image_path = temp_image.name

    filename = f"スロットデータ/画像_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    with open(temp_image_path, "rb") as f:
        upload_zip_to_dropbox(filename, f.read())

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="🖼️ 画像をDropboxに保存しました。")
    )

# ---------- Dropbox Webhook（自動解析＆通知） ----------
@app.route("/dropbox_webhook", methods=["POST"])
def handle_dropbox_webhook():
    try:
        # 保存先のZIPファイルを取得（例: 常に "latest_upload.zip"）
        path = "/Apps/slot-data-analyzer/latest_upload.zip"
        zip_data = download_file(path)
        result = analyze_zip_content(zip_data)

        # LINE通知（文字数制限）
        line_bot_api.push_message(USER_ID, TextSendMessage(text=result[:4000]))
        return "OK", 200

    except Exception as e:
        print(f"Webhookエラー: {e}")
        line_bot_api.push_message(USER_ID, TextSendMessage(text=f"⚠️ Webhook解析中にエラー発生: {e}"))
        return abort(500)

# ---------- ローカル実行用 ----------
if __name__ == "__main__":
    app.run(debug=True)