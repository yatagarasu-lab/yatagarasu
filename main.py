from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# 🔻 正しいチャネルアクセストークンとシークレットを入れてください
LINE_CHANNEL_ACCESS_TOKEN = 'あなたのチャネルアクセストークン'
LINE_CHANNEL_SECRET = 'あなたのチャネルシークレット'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.error("❌ Invalid signature. Check your channel access token/secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    message_text = event.message.text

    app.logger.info(f"✅ Received message from user {user_id}: {message_text}")

    # ユーザーに「ありがとうございます」と返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='ありがとうございます')
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)