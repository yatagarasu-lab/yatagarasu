from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage

import os
import tempfile
from dropbox_utils import upload_file
from analyzer import analyze_file

# 環境変数から取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
USER_ID = os.environ.get("LINE_USER_ID")

app = Flask(__name__)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

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
    text = event.message.text

    # Dropboxへ保存（ファイル名を生成）
    filename = f"text_{event.timestamp}.txt"
    upload_file(filename, text.encode('utf-8'))

    # GPT解析 → 結果を返信
    result = analyze_file(text.encode('utf-8'), filename)

    # LINEに送信
    line_bot_api.push_message(USER_ID, TextSendMessage(text=result or "ありがとうございます"))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)

    # 一時ファイル保存
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        temp_path = tf.name

    filename = f"image_{event.timestamp}.jpg"

    with open(temp_path, "rb") as f:
        file_bytes = f.read()
        upload_file(filename, file_bytes)

        result = analyze_file(file_bytes, filename)

    # LINEに送信
    line_bot_api.push_message(USER_ID, TextSendMessage(text=result or "ありがとうございます"))

    os.remove(temp_path)

@app.route("/")
def index():
    return "LINE + Dropbox + GPT Webhook is running"

if __name__ == "__main__":
    app.run(debug=True)