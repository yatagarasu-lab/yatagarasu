from flask import Flask, request, abort
import os
import hmac
import hashlib
import json
import dropbox_utils
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Flaskアプリケーションの起動
app = Flask(__name__)

# LINE設定（環境変数から取得）
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")  # Push通知を送る対象

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox Webhook受信用エンドポイント
@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        print("📩 DropboxからWebhook通知を受信しました")
        try:
            payload = request.get_data(as_text=True)
            print("通知内容:", payload)

            # 通知処理（LINEに送信）
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text="📦 Dropboxに新しい変更がありました。内容を確認してください。")
            )

            return '', 200
        except Exception as e:
            print(f"[エラー] Webhook処理失敗: {e}")
            return 'Error', 500

# LINE Webhook（ユーザーからのメッセージ受信）
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("📲 LINEからの受信内容:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ LINE署名検証に失敗しました")
        abort(400)

    return "OK"

# ユーザーからのLINEメッセージへの自動返信
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    message_text = event.message.text
    reply = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(debug=False)