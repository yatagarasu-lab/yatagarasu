import os
import hashlib
import dropbox
import openai
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

def list_files(folder_path="/Apps/slot-data-analyzer"):
    result = dbx.files_list_folder(folder_path)
    return result.entries

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)
        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

def analyze_file(content):
    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "あなたは画像や文章を解析して要約するAIです。"},
            {"role": "user", "content": "次の内容を解析して要約してください。"},
            {"role": "user", "content": content}
        ]
    )
    return response.choices[0].message.content.strip()

def send_line_message(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, json=data)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Webhook Received:", data)

    if "list_folder" not in data:
        print("ユーザーID取得失敗 or Pushエラー：'events'")
        return "OK"

    try:
        files = list_files()
        for file in files:
            content = download_file(file.path_display)
            summary = analyze_file(content.decode(errors="ignore"))
            send_line_message(f"📄 {file.name} の要約：\n{summary}")
        find_duplicates()
    except Exception as e:
        print("解析エラー:", e)

    return "OK"