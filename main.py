from flask import Flask, request, abort
import os
import hashlib
import hmac
import json
import dropbox
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINEのチャンネル設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ユーザーID（Push送信用）
LINE_USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"  # ←あなたのID

# Dropbox設定
DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

# Dropboxの変更通知Webhook（GET:検証 / POST:通知受信）
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox webhook認証用
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        print("📩 DropboxからWebhook受信")
        try:
            payload = request.get_data(as_text=True)
            print("内容:", payload)
            # ここでファイルの確認や通知などの処理を行う（省略）
            line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text="Dropboxに変更がありました"))
            return '', 200
        except Exception as e:
            print(f"Webhook処理中にエラー: {e}")
            return 'Error', 500

# LINE BotのWebhook
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

# LINEメッセージイベントの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    reply = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run()