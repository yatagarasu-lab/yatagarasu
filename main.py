from flask import Flask, request
from linebot.v4.messaging import MessagingApiClient, ReplyMessageRequest
from linebot.v4.webhook import WebhookHandler
from linebot.v4.models import TextMessage, TextMessageContent, MessageEvent
import os

app = Flask(__name__)

# 環境変数から取得（Renderの環境変数設定に登録しておくこと）
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

handler = WebhookHandler(channel_secret)
client = MessagingApiClient(channel_access_token)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return 'OK'

@handler.on(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessageContent):
        reply = TextMessage(text=f"あなたのメッセージ: {event.message.text}")
        client.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[reply]
            )
        )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)