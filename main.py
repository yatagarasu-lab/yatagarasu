import os
import sys
import base64
import requests
from flask import Flask, request, abort
from argparse import ArgumentParser
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage

app = Flask(__name__)

# 環境変数からLINEの設定情報を取得
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
openai_api_key = os.getenv('OPENAI_API_KEY')

if not channel_secret or not channel_access_token or not openai_api_key:
    print("環境変数が不足しています")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# Webhookのルーティング
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 画像受信時の処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    # LINEから画像取得
    message_id = event.message.id
    content = line_bot_api.get_message_content(message_id)
    image_data = content.content

    # Base64エンコード
    image_base64 = base64.b64encode(image_data).decode("utf-8")

    # ChatGPT APIへ画像送信
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {openai_api_key}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "この画像を要約・分析・予測してください。"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                    ]
                }
            ],
            "max_tokens": 1000
        }
    )

    # ChatGPTの応答をLINEへ返信
    if response.status_code == 200:
        reply = response.json()['choices'][0]['message']['content']
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="画像解析に失敗しました。"))

# ローカルテスト用（Renderでは使用されない）
if __name__ == "__main__":
    arg_parser = ArgumentParser()
    arg_parser.add_argument("-p", "--port", default=8000)
    options = arg_parser.parse_args()
    app.run(debug=True, port=options.port)