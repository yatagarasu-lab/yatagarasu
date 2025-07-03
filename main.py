from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 自分のチャネルアクセストークンとチャネルシークレットを入れてください
line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print("Request body: " + body)  # ← これもあると便利
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your channel access token/secret.")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_message = event.message.text

    # 👇ここが重要：ユーザーIDとメッセージをログに出す
    print(f"User ID: {user_id}")
    print(f"Message: {user_message}")

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='ありがとうございます')
    )

if __name__ == "__main__":
    app.run()