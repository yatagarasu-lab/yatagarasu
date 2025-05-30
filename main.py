from flask import Flask, request, abort
from linebot.v3.webhook import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.messaging.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

app = Flask(__name__)

# 環境変数からキー取得
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
openai.api_key = os.getenv("OPENAI_API_KEY")

# LINE API 設定
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print("Webhook受信:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("署名エラー")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    print("受信したメッセージ:", user_message)

    try:
        # OpenAI に問い合わせ
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_message}]
        )
        reply_text = response["choices"][0]["message"]["content"]

        print("GPTの返答:", reply_text)

        with ApiClient(configuration) as api_client:
            messaging_api = MessagingApi(api_client)
            messaging_api.reply_message(
                reply_token=event.reply_token,
                messages=[TextSendMessage(text=reply_text)]
            )

    except Exception as e:
        print("エラー発生:", e)

# Render用の起動コード
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)