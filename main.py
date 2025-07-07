from flask import Flask, request, abort
import os
import json
import hashlib
import hmac
import requests
import dropbox
from dropbox.files import WriteMode
from openai import OpenAI
import time

app = Flask(__name__)

# LINE Messaging API
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.environ.get("LINE_USER_ID")

# Dropbox（リフレッシュトークン使用）
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")
DROPBOX_ACCESS_TOKEN = None  # 起動時には未取得

# OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Dropboxアクセストークンを動的に取得
def get_dbx():
    global DROPBOX_ACCESS_TOKEN
    if DROPBOX_ACCESS_TOKEN is None:
        response = requests.post(
            "https://api.dropboxapi.com/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": DROPBOX_REFRESH_TOKEN,
                "client_id": DROPBOX_APP_KEY,
                "client_secret": DROPBOX_APP_SECRET,
            },
        )
        DROPBOX_ACCESS_TOKEN = response.json().get("access_token")
    return dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Dropbox Webhook
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge")
    elif request.method == "POST":
        print("✅ Dropbox webhook triggered")
        process_dropbox_folder()
        return "", 200

# Dropboxフォルダを処理（重複削除＋GPT解析＋LINE通知）
def process_dropbox_folder():
    dbx = get_dbx()
    folder_path = "/Apps/slot-data-analyzer"
    res = dbx.files_list_folder(folder_path)
    files = res.entries
    hash_map = {}

    for f in files:
        _, ext = os.path.splitext(f.name)
        if isinstance(f, dropbox.files.FileMetadata):
            metadata, res = dbx.files_download(f.path_display)
            content = res.content
            content_hash = hashlib.md5(content).hexdigest()

            if content_hash in hash_map:
                dbx.files_delete_v2(f.path_display)
                print(f"🗑️ Duplicate deleted: {f.name}")
                continue
            hash_map[content_hash] = f.path_display

            gpt_summary = query_gpt(content)
            notify_line(f"🧠 GPT解析結果: {f.name}\n{gpt_summary}")

# GPTに要約させる
def query_gpt(file_content):
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "あなたはDropboxから送られてきたファイル内容を要約し、内容の特徴を日本語で簡潔に説明するAIです。"},
            {"role": "user", "content": file_content.decode('utf-8')[:5000]},
        ],
        "temperature": 0.7,
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    result = response.json()
    return result["choices"][0]["message"]["content"]

# LINEに通知送信
def notify_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    res = requests.post(url, headers=headers, json=payload)
    print(f"📤 LINE通知送信: {res.status_code}")

@app.route("/")
def index():
    return "Server Running", 200