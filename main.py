from flask import Flask, request, abort
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, ReplyMessageRequest, TextMessage
from linebot.v3.webhook import WebhookHandler, WebhookParser
import os
import json

app = Flask(__name__)

channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        events = parser.parse(body, signature)
    except Exception as e:
        print("Webhook parsing error:", e)
        abort(400)

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        for event in events:
            if event.message and isinstance(event.message, TextMessage):
                reply_token = event.reply_token
                text = event.message.text
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=reply_token,
                        messages=[TextMessage(text=f"あなたのメッセージ: {text}")]
                    )
                )
    return 'OK'