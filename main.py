import os
import hashlib
import json
from flask import Flask, request, jsonify
import dropbox
import openai
import requests

app = Flask(__name__)

# 環境変数から取得
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

# ファイル一覧取得
def list_files(folder_path):
    files = []
    result = dbx.files_list_folder(folder_path)
    files.extend(result.entries)
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        files.extend(result.entries)
    return files

# ファイル内容取得
def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

# ハッシュ生成
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# LINE通知
def send_line_message(message):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, data=json.dumps(data))

# GPT要約
def summarize_content(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下の内容を日本語で簡潔に要約してください。"},
                {"role": "user", "content": content.decode("utf-8", errors="ignore")}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"要約失敗: {str(e)}"

# 重複チェック＆処理
def handle_new_files():
    files = list_files("/Apps/slot-data-analyzer")
    hash_map = {}
    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            path = file.path_display
            content = download_file(path)
            hash_value = file_hash(content)

            if hash_value in hash_map:
                # 重複 → 削除
                dbx.files_delete_v2(path)
                continue
            else:
                hash_map[hash_value] = path
                # GPTで要約
                summary = summarize_content(content)
                # LINE通知
                send_line_message(f"🗂 新ファイル: {file.name}\n📄 要約:\n{summary}")
                # 処理済みフォルダへ移動
                new_path = "/Apps/slot-data-analyzer/processed/" + file.name
                dbx.files_move_v2(from_path=path, to_path=new_path, allow_shared_folder=True, autorename=True)

# Webhook受信処理
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge")
    elif request.method == "POST":
        print("Dropbox Webhook received.")
        handle_new_files()
        return "", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)