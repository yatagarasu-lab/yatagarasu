import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import MessagingApiClient, ReplyMessageRequest
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

app = Flask(__name__)

# チャネルシークレットとアクセストークン
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = MessagingApiClient(channel_access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Error:", e)
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event):
    message = event.message.text
    reply = f"あなたのメッセージ: {message}"
    client.reply_message(
        ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[{
                "type": "text",
                "text": reply
            }]
        )
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)