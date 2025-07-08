import os
import hashlib
import base64
import dropbox
from flask import Flask, request, abort

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from openai import OpenAI

app = Flask(__name__)

# LINE設定
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
user_id = os.getenv("LINE_USER_ID")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# OpenAI設定
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Dropbox設定
dropbox_token = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(dropbox_token)

# GPT解析関数
def analyze_with_gpt(text):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "これはLINEやDropboxから送られた分析データです。要約・分析してください。"},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.strip()

# Dropbox保存
def save_to_dropbox(filename, content):
    path = f"/Apps/slot-data-analyzer/{filename}"
    dbx.files_upload(content.encode("utf-8"), path, mode=dropbox.files.WriteMode.overwrite)

# 署名検証付きLINE処理
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    if signature:
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            abort(400)
        return "OK"

    # ← 署名なし：Dropbox通知や手動送信テキスト等として処理
    print("署名なしリクエスト受信：GPT解析へ回します")
    data = request.get_json()

    # 内容を文字列化して解析
    raw_text = str(data)
    result = analyze_with_gpt(raw_text)

    # Dropboxに保存
    filename = f"dropbox_analysis_{hashlib.md5(raw_text.encode()).hexdigest()[:8]}.txt"
    save_to_dropbox(filename, result)

    # LINEに返信（Push通知）
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(user_id, [
            {
                "type": "text",
                "text": f"Dropbox通知を解析しました：\n{result[:100]}..."
            }
        ])

    return "OK", 200

# LINEでテキスト受信時の処理
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    text = event.message.text
    result = analyze_with_gpt(text)

    # Dropbox保存
    filename = f"line_message_{hashlib.md5(text.encode()).hexdigest()[:8]}.txt"
    save_to_dropbox(filename, result)

    # LINE返信
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(event.reply_token, [
            {
                "type": "text",
                "text": f"ありがとうございます"
            }
        ])