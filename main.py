import os
from flask import Flask, request, abort

from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration
from linebot.v3.models import MessageEvent, TextMessage, TextMessageContent
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# 環境変数からトークンとシークレットを取得
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)
line_bot_api = MessagingApi(configuration)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextMessage(text="こんにちは！テスト応答です✨")
        ]
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))