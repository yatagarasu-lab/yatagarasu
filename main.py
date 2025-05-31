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

# .env 読み込み
load_dotenv()

# Flask初期化
app = Flask(__name__)

# LINE API
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
if not channel_secret or not channel_access_token:
    print("LINEの環境変数が見つかりません")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

# OpenAI API
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 最後の受信記録
last_received_time = datetime.utcnow()

# 5分後に返信
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

    # OpenAI 新バージョンの使用
    client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたはLINEで受け取ったメッセージを分析するAIです。要約し、予測は聞かれたときのみ行ってください。"},
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
    image_data = io.BytesIO(content.content)

    base64_image = base64.b64encode(image_data.getvalue()).decode("utf-8")
    image_url = f"data:image/jpeg;base64,{base64_image}"

    # 新API仕様（gpt-4-vision-preview）
    client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "この画像の内容を要約してください"},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]
            }
        ]
    )

    threading.Thread(target=delayed_reply, args=(event.source.user_id,)).start()

if __name__ == "__main__":
    app.run()