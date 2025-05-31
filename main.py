from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage

from openai import OpenAI
import os
import requests

# .envなどから読み込む場合はdotenv使用（Renderでは環境変数として設定推奨）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

app = Flask(__name__)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_text = event.message.text

    # ChatGPTで返答を生成
    response = client.chat.completions.create(
        model="gpt-4",  # または "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "あなたは親切なアシスタントです。"},
            {"role": "user", "content": user_text}
        ]
    )

    reply_text = response.choices[0].message.content.strip()

    # LINEへ返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    # ユーザーが送った画像のURL取得
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = b''.join(chunk for chunk in message_content.iter_content())

    # OpenAIに画像＋質問を送る場合の準備（必要に応じて調整）
    # 現在は画像保存・固定応答のサンプルのみ
    with open("temp.jpg", "wb") as f:
        f.write(image_data)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="画像を受け取りました。ありがとうございます。")
    )

if __name__ == "__main__":
    app.run()