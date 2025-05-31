import os
import sys
import time
import base64
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import openai

# Flaskアプリ起動
app = Flask(__name__)

# 環境変数取得
channel_secret = os.getenv('LINE_CHANNEL_SECRET')
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
openai_api_key = os.getenv('OPENAI_API_KEY')

# 確認
if channel_secret is None or channel_access_token is None:
    print('環境変数が不足しています')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)
openai.api_key = openai_api_key

# 応答タイミング制御用
last_received_time = 0
waiting_reply_user_id = None

@app.route("/callback", methods=['POST'])
def callback():
    global last_received_time, waiting_reply_user_id

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
    global last_received_time, waiting_reply_user_id
    user_text = event.message.text
    waiting_reply_user_id = event.source.user_id
    last_received_time = time.time()

    # ChatGPTに送信（返信はしない）
    openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "LINEからのメッセージを分析して下さい。"},
            {"role": "user", "content": user_text}
        ]
    )

# 画像メッセージ処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    global last_received_time, waiting_reply_user_id
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = b''.join(chunk for chunk in message_content.iter_content())
    base64_image = base64.b64encode(image_data).decode('utf-8')
    waiting_reply_user_id = event.source.user_id
    last_received_time = time.time()

    # ChatGPT Visionに送信
    openai.ChatCompletion.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "system", "content": "画像の内容を分析してください。"},
            {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}]}
        ]
    )

# 自動返信チェック（RenderのCron Jobや外部アクセスで定期実行）
@app.route("/check", methods=["GET"])
def check_reply():
    global last_received_time, waiting_reply_user_id

    if waiting_reply_user_id and (time.time() - last_received_time > 300):
        line_bot_api.push_message(waiting_reply_user_id, TextSendMessage(text="ありがとうございます"))
        waiting_reply_user_id = None
        return "返信しました"
    return "まだ返信しません"

if __name__ == "__main__":
    app.run()