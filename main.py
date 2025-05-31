import os
import sys
import time
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import openai
from io import BytesIO
import requests
from threading import Timer

app = Flask(__name__)

# LINE環境変数
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
if channel_secret is None or channel_access_token is None:
    print("環境変数が設定されていません")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# OpenAI環境変数
openai.api_key = os.getenv("OPENAI_API_KEY")

# 返信遅延のためのタイマー
reply_timer = None

def delayed_reply(reply_token):
    try:
        line_bot_api.reply_message(reply_token, TextSendMessage(text="ありがとうございます"))
    except Exception as e:
        print(f"返信エラー: {e}")

def reset_timer(reply_token):
    global reply_timer
    if reply_timer:
        reply_timer.cancel()
    reply_timer = Timer(300, delayed_reply, [reply_token])  # 5分後に返信
    reply_timer.start()

def analyze_with_gpt(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "スロットの設定分析と店舗傾向分析に使うためのテキストや画像の要約・解析を行ってください。"
                },
                {
                    "role": "user",
                    "content": content
                }
            ]
        )
        result = response['choices'][0]['message']['content']
        print(f"GPT解析結果: {result}")
        return result
    except Exception as e:
        print(f"OpenAI APIエラー: {e}")
        return None

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
def handle_text_message(event):
    text = event.message.text
    analyze_with_gpt(text)
    reset_timer(event.reply_token)

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = BytesIO(message_content.content)
    analyze_with_gpt("画像が送信されました。スロットの設定や傾向に関する内容を含むかもしれません。")
    reset_timer(event.reply_token)

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port)