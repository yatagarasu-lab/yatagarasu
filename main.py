import os
import hashlib
import dropbox
from flask import Flask, request
import openai
import requests

# 環境変数から読み込む（Renderで設定済みのもの）
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

app = Flask(__name__)

# Dropbox 接続
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

def list_files(folder_path="/Apps/slot-data-analyzer"):
    result = dbx.files_list_folder(folder_path)
    return result.entries

def download_file(file_path):
    _, res = dbx.files_download(file_path)
    return res.content

def file_hash(file_content):
    return hashlib.sha256(file_content).hexdigest()

def notify_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, json=body)

def analyze_with_gpt(file_text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "これはDropboxにアップロードされたスロット関連のデータです。内容を要約し、重要な点を抽出してください。"},
            {"role": "user", "content": file_text}
        ]
    )
    return response.choices[0].message.content

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
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

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox Verification 用
        challenge = request.args.get("challenge")
        return challenge, 200

    elif request.method == "POST":
        try:
            # 重複を削除
            find_duplicates()
            notify_line("Dropboxにファイルが追加されました。解析を開始します。")
            return "Webhook受信済み", 200
        except Exception as e:
            notify_line(f"エラー発生: {str(e)}")
            return "エラー", 500

    return "無効なリクエスト", 400

@app.route("/", methods=["GET"])
def home():
    return "動作中（Slot GPT Analyzer）", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)