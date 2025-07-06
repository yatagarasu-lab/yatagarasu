from flask import Flask, request
import os
import dropbox
import hashlib
import base64
import requests

app = Flask(__name__)

# 環境変数
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Dropbox 初期化
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Dropbox からファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

# Dropbox ファイルのダウンロード
def download_file(file_path):
    _, res = dbx.files_download(file_path)
    return res.content

# SHA256 で重複チェック
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# GPT要約
def summarize_with_gpt(file_bytes):
    from openai import OpenAI
    client = OpenAI()

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "以下のファイル内容を要約してください。"},
            {"role": "user", "content": file_bytes.decode('utf-8', errors='ignore')}
        ],
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()

# LINE Push 通知
def send_line_message(message):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)

# ホームページ表示用（Render動作確認）
@app.route("/", methods=["GET"])
def home():
    return "✅ GPT×Dropbox×LINE Bot は起動中です", 200

# Dropbox Webhook エンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    folder_path = "/Apps/slot-data-analyzer"
    files = list_files(folder_path)
    hash_map = {}

    summary_report = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            dbx.files_delete_v2(path)
            summary_report.append(f"🗑️ 重複ファイル削除: {path}")
        else:
            hash_map[hash_value] = path
            summary = summarize_with_gpt(content)
            summary_report.append(f"📄 {path}:\n{summary}\n")

    final_report = "\n\n".join(summary_report) if summary_report else "変更が検出されましたが、処理対象はありませんでした。"
    send_line_message(final_report[:499])  # LINE制限対策
    return "OK", 200
    from flask import Flask, request
import os

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ GPT×Dropbox×LINE Bot は起動中です", 200

# ここに他のWebhook処理などが続くはず…