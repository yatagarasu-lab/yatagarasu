from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import os
import requests
import hashlib
import dropbox
from gpt_utils import process_with_gpt  # 外部ファイルでGPT処理を管理

# Flask初期化
app = Flask(__name__)

# 環境変数からLINEとDropboxのキーを取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")

# LINE Bot初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropboxクライアント
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# LINEのWebhookエンドポイント（POST）
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# LINEのメッセージ処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text

    # Dropboxに保存
    filename = f"{user_id}_{event.timestamp}.txt"
    dbx.files_upload(text.encode(), f"/スロットデータ/{filename}")

    # GPTで処理
    gpt_result = process_with_gpt(text)

    # LINE返信
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text="ありがとうございます")  # 固定返信
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    message_id = event.message.id

    # 画像取得
    image_content = line_bot_api.get_message_content(message_id).content
    filename = f"{user_id}_{message_id}.jpg"

    # Dropbox保存
    dbx.files_upload(image_content, f"/スロットデータ/{filename}")

    # GPTで処理（オプション）
    # process_with_gpt_image(image_content)

    # 返信
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text="ありがとうございます")
    )

# DropboxのWebhook検証用（GET）
@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        # 通知は空応答でもOK（処理は後でpollingでも可能）
        return "OK", 200

# ルート確認用
@app.route("/", methods=["GET"])
def health_check():
    return "LINE-Dropbox GPT Bot is running", 200