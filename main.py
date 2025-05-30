import os
from flask import Flask, request, abort

from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging_api import MessagingApiClient
from linebot.v3.models import TextMessage, ReplyMessageRequest, MessageEvent, TextMessageContent

# Flask アプリ起動
app = Flask(__name__)

# 環境変数からキー取得
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

# LINE SDK 初期化
handler = WebhookHandler(channel_secret)
messaging_api = MessagingApiClient(channel_access_token)

# Webhookエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"[ERROR] handler error: {e}")
        abort(400)

    return 'OK'

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    user_message = event.message.text

    reply = ReplyMessageRequest(
        reply_token=event.reply_token,
        messages=[TextMessage(text=f"あなたのメッセージ: {user_message}")]
    )
    messaging_api.reply_message(reply)

# ローカルテスト用（Renderでは使われません）
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)