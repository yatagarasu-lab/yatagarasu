import os
import json
import hashlib
import dropbox
import openai
import requests
from flask import Flask, request

app = Flask(__name__)

# .env読み込み
from dotenv import load_dotenv
load_dotenv()

# LINE
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Dropbox
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")


def get_dropbox_access_token():
    url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_APP_KEY,
        "client_secret": DROPBOX_APP_SECRET,
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")


def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = dropbox.Dropbox(get_dropbox_access_token())
    result = dbx.files_list_folder(folder_path)
    return result.entries


def download_file(path):
    dbx = dropbox.Dropbox(get_dropbox_access_token())
    metadata, res = dbx.files_download(path)
    return res.content


def file_hash(content):
    return hashlib.sha256(content).hexdigest()


def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    duplicates = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            duplicates.append((path, hash_map[hash_value]))
            dbx = dropbox.Dropbox(get_dropbox_access_token())
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

    return duplicates


def analyze_file(path):
    content = download_file(path)
    try:
        text = content.decode("utf-8")
    except:
        text = "画像またはバイナリファイル（解析対象外）"
    prompt = f"次のデータを要約して下さい:\n\n{text[:4000]}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()


def send_line_notify(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}],
    }
    requests.post(url, headers=headers, json=data)


@app.route("/webhook", methods=["POST"])
def webhook():
    # Dropbox Webhookで通知があったらファイルを調査
    folder_path = "/Apps/slot-data-analyzer"
    files = list_files(folder_path)
    if not files:
        return "No files found", 200

    latest_file = sorted(files, key=lambda f: f.server_modified, reverse=True)[0]
    result = analyze_file(latest_file.path_display)
    duplicates = find_duplicates(folder_path)

    # 通知作成
    message = f"🗂️ 新しいファイルを解析しました！\n\n📄 ファイル名: {latest_file.name}\n\n📝 要約:\n{result}"
    if duplicates:
        message += f"\n\n⚠️ 重複ファイル {len(duplicates)} 件削除済み"

    send_line_notify(message)
    return "OK", 200


@app.route("/", methods=["GET"])
def index():
    return "Dropbox × GPT × LINE Bot は動作中です。", 200


if __name__ == "__main__":
    app.run(debug=True)