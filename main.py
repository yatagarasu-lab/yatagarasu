from flask import Flask, request, abort
import os
import json
import hmac
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from dropbox_handler import process_dropbox_changes

app = Flask(__name__)

# 環境変数からLINE設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ✅ Dropbox Webhook（検証用GET + 通知受信用POST）
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # DropboxのWebhook認証
        return request.args.get("challenge"), 200

    if request.method == "POST":
        print("📩 Dropbox Webhook受信")
        try:
            process_dropbox_changes()
            return '', 200
        except Exception as e:
            print(f"Dropbox変更処理中にエラー: {e}")
            return 'Error', 500

# ✅ LINE BOT Webhook（不要なら消してOK）
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("LINEメッセージ受信:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ✅ LINE受信メッセージに固定返信（BOTテスト用）
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    reply = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run()