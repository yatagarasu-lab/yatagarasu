import os
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from openai import OpenAI
from PIL import Image
from io import BytesIO
import dropbox
from datetime import datetime

app = Flask(__name__)

# 環境変数の読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
DROPBOX_CLIENT_ID = os.environ['DROPBOX_CLIENT_ID']
DROPBOX_CLIENT_SECRET = os.environ['DROPBOX_CLIENT_SECRET']
DROPBOX_REFRESH_TOKEN = os.environ['DROPBOX_REFRESH_TOKEN']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropboxアクセストークン取得
def get_dropbox_access_token():
    url = "https://api.dropboxapi.com/oauth2/token"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': DROPBOX_REFRESH_TOKEN,
        'client_id': DROPBOX_CLIENT_ID,
        'client_secret': DROPBOX_CLIENT_SECRET,
    }
    res = requests.post(url, headers=headers, data=data)
    return res.json().get('access_token')

# Dropboxへファイルアップロード
def upload_to_dropbox(file_bytes, file_name):
    access_token = get_dropbox_access_token()
    dbx = dropbox.Dropbox(access_token)
    now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    dropbox_path = f"/スロットデータ/{now}_{file_name}"
    dbx.files_upload(file_bytes, dropbox_path)
    return dropbox_path

# GPTで解析（テキスト or 画像要約）
def analyze_with_gpt(prompt):
    client = OpenAI(api_key=OPENAI_API_KEY)
    chat_completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )
    return chat_completion.choices[0].message.content.strip()

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 画像受信処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id)
    image_bytes = BytesIO(image_content.content).getvalue()
    
    # Dropboxに保存
    filename = f"{message_id}.jpg"
    upload_to_dropbox(image_bytes, filename)

    # GPTで要約（画像の内容を記述する指示）
    prompt = "この画像の内容を要約して下さい。スロットのグラフならその設定を推測してください。"
    result = analyze_with_gpt(prompt)

    # LINE返信
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))

# テキスト受信処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_text = event.message.text
    # Dropboxに保存
    upload_to_dropbox(user_text.encode(), f"{event.message.id}.txt")

    # GPTで解析
    result = analyze_with_gpt(f"以下のテキストを解析し、要点と意味を説明してください：\n\n{user_text}")
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))

# 動作確認用ルート
@app.route("/", methods=['GET'])
def index():
    return "GPT × LINE × Dropbox BOT is running."

if __name__ == "__main__":
    app.run()