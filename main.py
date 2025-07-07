from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import json

app = Flask(__name__)

# LINE用の環境変数
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ✅ Webhook（共通）Dropbox or LINEを分岐処理
@app.route("/webhook", methods=["POST"])
def webhook():
    # DropboxからのWebhookか判定
    if "X-Line-Signature" not in request.headers:
        # Dropbox確認用（Challengeのレスポンス用）
        if request.args.get("challenge"):
            return request.args.get("challenge")

        try:
            json_data = request.get_json()
            print("[Dropbox Webhook 受信]", json_data)
            # 必要に応じてDropbox処理をここで追加
            return "Dropbox Webhook received", 200
        except Exception as e:
            print("Dropbox Webhook error:", e)
            return "Error", 500

    # LINE BOT用
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# LINE BOT用メッセージ処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply_text = "ありがとうございます"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# 動作確認用
@app.route("/", methods=["GET"])
def index():
    return "LINE + Dropbox Webhook is running."

if __name__ == "__main__":
    app.run()