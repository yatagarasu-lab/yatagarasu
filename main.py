import os
import sys
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from PIL import Image
import dropbox
import openai
from io import BytesIO
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Flask アプリ初期化
app = Flask(__name__)

# LINE BOT設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
USER_ID = os.getenv("LINE_USER_ID")  # Push通知用

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# OpenAI設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# Dropboxフォルダ
FOLDER_PATH = "/Apps/slot-data-analyzer"

# ファイルのハッシュで重複チェック
def file_hash(content):
    return hashlib.md5(content).hexdigest()

def list_files(folder_path):
    result = dbx.files_list_folder(folder_path)
    return result.entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def find_duplicates(folder_path=FOLDER_PATH):
    files = list_files(folder_path)
    hash_map = {}
    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)
        if hash_value in hash_map:
            dbx.files_delete_v2(path)  # 重複ファイルを削除
        else:
            hash_map[hash_value] = path

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
def handle_text_message(event):
    text = event.message.text
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "このメッセージを要約してください"},
            {"role": "user", "content": text}
        ]
    )
    summary = response.choices[0].message.content
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=summary))

# 画像メッセージ処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id)
    image_bytes = BytesIO(image_content.content)

    # Pillowで画像確認（不要なら削除可能）
    image = Image.open(image_bytes)

    # Dropboxへ保存
    file_path = f"{FOLDER_PATH}/image_{message_id}.jpg"
    dbx.files_upload(image_content.content, file_path)

    # 重複ファイルの整理
    find_duplicates()

    # GPTで通知内容生成
    gpt_response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "これはユーザーから受け取った画像です。Dropboxに保存済みなので、通知文を生成してください。"},
            {"role": "user", "content": f"{file_path} が保存されました。"}
        ]
    )
    reply_text = gpt_response.choices[0].message.content

    # LINEへPush通知
    line_bot_api.push_message(USER_ID, TextSendMessage(text=reply_text))

# Render用起動ポイント
if __name__ == "__main__":
    app.run()