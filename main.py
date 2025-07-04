import os
import hashlib
import dropbox
import requests
from flask import Flask, request
from dotenv import load_dotenv
from openai import OpenAI
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage

# .env読み込み
load_dotenv()

# 環境変数
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_USER_ID = os.getenv("LINE_USER_ID")  # push用

# 初期化
app = Flask(__name__)
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai = OpenAI(api_key=OPENAI_API_KEY)

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def upload_to_dropbox(filename, content):
    path = f"/Apps/slot-data-analyzer/{filename}"
    dbx.files_upload(content, path, mode=dropbox.files.WriteMode.overwrite)
    return path

def summarize_text(text):
    prompt = f"次の文章を要約してください：\n{text}"
    res = openai.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return res.choices[0].message.content.strip()

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    handler.handle(body, signature)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_text = event.message.text
    summary = summarize_text(user_text)

    filename = f"text_{hashlib.md5(user_text.encode()).hexdigest()}.txt"
    upload_to_dropbox(filename, user_text.encode())

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

    # Pushで要約通知
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=f"[自動要約]\n{summary}")
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = b"".join(chunk for chunk in message_content.iter_content(chunk_size=1024))

    filename = f"image_{event.message.id}.jpg"
    upload_to_dropbox(filename, image_data)

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

    # Push通知（画像名だけ）
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=f"[画像受信] {filename} をDropboxに保存しました")
    )

if __name__ == "__main__":
    app.run(debug=False)