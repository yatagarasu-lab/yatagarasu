from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage

from handlers.handle_text_message import handle_text_message
from handlers.handle_image_message import handle_image_message

import os

# 環境変数からアクセストークンとシークレットを取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

app = Flask(__name__)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/callback", methods=["POST"])
def callback():
    # X-Line-Signatureヘッダーから署名を取得
    signature = request.headers["X-Line-Signature"]

    # リクエストボディを取得
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent)
def handle_message(event):
    if isinstance(event.message, TextMessage):
        handle_text_message(event, line_bot_api)
    elif isinstance(event.message, ImageMessage):
        handle_image_message(event, line_bot_api)


if __name__ == "__main__":
    app.run()