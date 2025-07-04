import os
import hashlib
import dropbox
import openai
import requests
from flask import Flask, request
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage

# 環境変数の読み込み
load_dotenv()

# LINE
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Dropbox
dbx = dropbox.Dropbox(
    oauth2_refresh_token=os.getenv("DROPBOX_REFRESH_TOKEN"),
    app_key=os.getenv("DROPBOX_APP_KEY"),
    app_secret=os.getenv("DROPBOX_APP_SECRET")
)

# OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

def summarize_content(content):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたはファイル要約のアシスタントです。"},
            {"role": "user", "content": f"次の内容を要約してください：\n\n{content[:4000]}"}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

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

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    for entry in data.get("list_folder", {}).get("entries", []):
        if entry[0] != "file":
            continue
        file_path = entry[1]["path_display"]
        content = download_file(file_path)
        summary = summarize_content(content.decode("utf-8", errors="ignore"))
        find_duplicates()  # 重複削除実行
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=f"📁 {file_path} の解析結果:\n\n{summary}")
        )
    return "OK", 200

@app.route("/", methods=["GET"])
def health_check():
    return "Webhook is running!", 200

if __name__ == "__main__":
    app.run(debug=True)