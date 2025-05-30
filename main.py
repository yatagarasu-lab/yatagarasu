from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import openai

# Flaskアプリ作成
app = Flask(__name__)

# 環境変数から各種キーを取得
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")

# LINEのWebhookエンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# ユーザーからのメッセージを処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # ChatGPTへ問い合わせ
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    # GPTの返答を取り出す
    reply_text = response["choices"][0]["message"]["content"]
    print("GPTの返答:", reply_text)  # ←デバッグ用

    # LINEへ返信
    reply = TextSendMessage(text=reply_text)
    line_bot_api.reply_message(event.reply_token, reply)

# アプリ起動（Renderでは必要なし）
# if __name__ == "__main__":
#     app.run()