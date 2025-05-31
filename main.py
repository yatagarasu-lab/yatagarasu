import os
import time
import threading
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage
from openai import OpenAI
from dotenv import load_dotenv
import base64

# 環境変数の読み込み
load_dotenv()
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

def handle_image(event):
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id)
    image_path = f"/tmp/{message_id}.jpg"

    with open(image_path, 'wb') as f:
        for chunk in image_content.iter_content():
            f.write(chunk)

    # 画像をBase64エンコードしてOpenAIに送る
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "system", "content": "あなたは画像を分析するアシスタントです。"},
            {"role": "user", "content": [
                {"type": "text", "text": "この画像の内容を要約して下さい。"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]}
        ],
        max_tokens=300
    )

    print(response.choices[0].message.content)  # ログ用

    # 5分後に返信
    def delayed_reply():
        time.sleep(300)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ありがとうございます")
        )

    threading.Thread(target=delayed_reply).start()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=ImageMessage)
def handle_message(event):
    handle_image(event)

if __name__ == "__main__":
    app.run()