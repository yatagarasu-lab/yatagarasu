from flask import Flask, request, abort
import os
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from dropbox_utils import list_files
from gpt_analyzer import analyze_and_notify

app = Flask(__name__)

# LINE設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")  # Push送信先
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge"), 200

    if request.method == "POST":
        try:
            print("✅ Dropbox Webhook受信")
            analyze_and_notify(line_bot_api, LINE_USER_ID)
            return '', 200
        except Exception as e:
            print(f"Webhookエラー: {e}")
            return 'Error', 500

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("📩 LINEメッセージ:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

if __name__ == "__main__":
    app.run()