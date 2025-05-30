from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os

# Flaskアプリ作成
app = Flask(__name__)

# 環境変数からAPIキー取得
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")

# Webhookエンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print("Webhook受信:", body)  # デバッグ用

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("署名エラー")
        abort(400)

    return 'OK'

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    print("受信したメッセージ:", user_message)  # デバッグ用

    try:
        # ChatGPTに問い合わせ
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        reply_text = response["choices"][0]["message"]["content"]
        print("GPTの返答:", reply_text)  # デバッグ用

        # LINEへ返信
        reply = TextSendMessage(text=reply_text)
        line_bot_api.reply_message(event.reply_token, reply)

    except Exception as e:
        print("エラー発生:", e)

# Renderでは起動記述不要（ローカル用）
# if __name__ == "__main__":
#     app.run()