from flask import Flask, request, abort
import os
import hashlib
import hmac
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dropbox_handler import handle_new_files

app = Flask(__name__)

# LINE設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Dropbox Webhook（検証＋通知）
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        print("📩 DropboxからWebhook通知を受信")
        try:
            # ここでGPT解析を実行
            result = handle_new_files()
            return "OK", 200
        except Exception as e:
            print(f"❌ Webhook処理エラー: {e}")
            return "Error", 500

# LINE Bot Webhook（ユーザーからのメッセージ受信）
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    print("📨 LINEメッセージ:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# LINEメッセージ応答
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

if __name__ == "__main__":
    app.run()