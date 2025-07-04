from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage

import os
import dropbox
import openai
from dotenv import load_dotenv
import requests
import hashlib
import base64
from PIL import Image
from io import BytesIO

# 環境変数の読み込み
load_dotenv()

# LINE APIキー
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

# Dropboxアクセストークン
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

# OpenAI APIキー
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# Flaskアプリ起動
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)


# Dropboxにファイルアップロード
def upload_to_dropbox(file_data, filename):
    path = f"/Apps/slot-data-analyzer/{filename}"
    dbx.files_upload(file_data, path, mode=dropbox.files.WriteMode("overwrite"))
    return path


# ファイルの重複チェック用ハッシュ
def file_hash(file_data):
    return hashlib.md5(file_data).hexdigest()


# 重複ファイル検出・削除
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = dbx.files_list_folder(folder_path).entries
    hash_map = {}

    for file in files:
        path = file.path_display
        metadata, res = dbx.files_download(path)
        content = res.content
        hash_value = file_hash(content)

        if hash_value in hash_map:
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path


# 画像やテキストのGPT要約
def summarize_content(content):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "これはLINE BOT経由で送信されたデータの要約タスクです。"},
            {"role": "user", "content": content}
        ]
    )
    return response.choices[0].message.content.strip()


# LINE webhookルート
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    filename = f"text_{event.timestamp}.txt"
    upload_to_dropbox(text.encode("utf-8"), filename)

    summary = summarize_content(text)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"要約:\n{summary}")
    )


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = message_content.content
    filename = f"image_{event.timestamp}.jpg"
    upload_to_dropbox(image_data, filename)

    # GPTへの簡易送信（画像説明目的）
    gpt_summary = summarize_content("画像がアップロードされました。内容を後ほど解析します。")

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"画像を保存しました。\n{gpt_summary}")
    )


# Gunicorn起動用
if __name__ == "__main__":
    app.run()