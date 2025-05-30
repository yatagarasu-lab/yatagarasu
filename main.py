from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler
from linebot.v3.webhooks import MessageEvent
import os

app = Flask(__name__)

# 環境変数からトークンとシークレットを取得
line_bot_api = MessagingApiClient(channel_access_token=os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        abort(400)

    return 'OK'

# メッセージイベントを処理
@handler.add(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessage):
        message = TextMessage(text="こんにちは！")
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[message]
            )
        )

# Flaskアプリを gunicorn が認識できるように定義
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)