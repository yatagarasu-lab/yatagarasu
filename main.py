import os
import sys
import time
import io
import threading
import base64
from datetime import datetime, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import openai
from dotenv import load_dotenv

load_dotenv()

# Flaskアプリの初期化
app = Flask(__name__)

# LINE API初期化
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
if not channel_secret or not channel_access_token:
    print("Specify LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# OpenAI初期化
openai.api_key = os.getenv('OPENAI_API_KEY')

# 最後のメッセージ時間の記録
last_received_time = datetime.utcnow()

# 5分後に返信する関数
def delayed_reply(user_id):
    global last_received_time
    while True:
        now = datetime.utcnow()
        if (now - last_received_time) >= timedelta(minutes=5):
            line_bot_api.push_message(user_id, TextMessage(text="ありがとうございます"))
            break
        time.sleep(30)

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
    global last_received_time
    last_received_time = datetime.utcnow()

    user_text = event.message.text
    _ = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたはLINEで受け取ったメッセージを分析するAIです。内容を要約し、予測は求められたときのみ返答します。"},
            {"role": "user", "content": user_text}
        ]
    )
    threading.Thread(target=delayed_reply, args=(event.source.user_id,)).start()

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    global last_received_time
    last_received_time = datetime.utcnow()

    message_id = event.message.id
    content = line_bot_api.get_message_content(message_id)
    image_data = base64.b64encode(content.content).decode('utf-8')

    _ = openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "この画像の内容を要約してください"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            }
        ]
    )
    threading.Thread(target=delayed_reply, args=(event.source.user_id,)).start()

if __name__ == "__main__":
    app.run()