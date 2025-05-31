import os
import sys
import time
import io
import base64
import threading
from datetime import datetime, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# LINE API
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
if not channel_secret or not channel_access_token:
    print("Missing LINE credentials")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# OpenAI API
openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)

# 最後のメッセージ時間記録
last_received_time = datetime.utcnow()

# 5分後に1回だけ返信
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

# テキストメッセージ処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    global last_received_time
    last_received_time = datetime.utcnow()

    user_text = event.message.text
    _ = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたはLINEで受け取ったメッセージを分析するAIです。要約や解釈を行い、予測は聞かれた時だけ答えてください。"},
            {"role": "user", "content": user_text}
        ]
    )

    threading.Thread(target=delayed_reply, args=(event.source.user_id,)).start()

# 画像メッセージ処理（vision対応）
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    global last_received_time
    last_received_time = datetime.utcnow()

    message_id = event.message.id
    content = line_bot_api.get_message_content(message_id)
    image_bytes = content.content
    b64_image = base64.b64encode(image_bytes).decode('utf-8')
    image_url = f"data:image/jpeg;base64,{b64_image}"

    _ = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "この画像を要約してください"},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ]
    )

    threading.Thread(target=delayed_reply, args=(event.source.user_id,)).start()

if __name__ == "__main__":
    app.run()