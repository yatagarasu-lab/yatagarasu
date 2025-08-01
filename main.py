import os
import json
import dropbox
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage
)
from openai import OpenAI
from io import BytesIO
from datetime import datetime

# --- 環境変数からキーを取得 ---
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_USER_ID = os.getenv("LINE_USER_ID", "")  # Push送信用に任意

# --- Flaskアプリケーション作成 ---
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai = OpenAI(api_key=OPENAI_API_KEY)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# --- メインWebhookエンドポイント ---
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# --- メッセージイベント処理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_text = event.message.text

    # GPTによる要約（または固定返信に変更可能）
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_text}]
        )
        reply = response.choices[0].message.content.strip()
    except Exception:
        reply = "ありがとうございます"

    # 返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id)

    # 保存ファイル名とDropboxパス
    now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{now}_{message_id}.jpg"
    dropbox_path = f"/Apps/slot-data-analyzer/{filename}"

    # Dropboxへアップロード
    dbx.files_upload(image_content.content, dropbox_path)

    # 返信（固定）
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます（画像を保存しました）")
    )

# --- Push通知の例（任意） ---
@app.route("/push", methods=['GET'])
def push_test():
    if LINE_USER_ID:
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text="Push通知テストです！")
        )
        return "Push sent"
    else:
        return "LINE_USER_ID not set"

# --- アプリ起動 ---
if __name__ == "__main__":
    app.run()