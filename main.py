from flask import Flask, request
import dropbox
import hashlib
import os
import openai
from linebot import LineBotApi
from linebot.models import TextSendMessage
from datetime import datetime

# 環境変数から取得
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
MONITOR_FOLDER_PATH = "/Apps/slot-data-analyzer"

# 初期化
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
app = Flask(__name__)

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def list_files(folder_path=MONITOR_FOLDER_PATH):
    files = []
    result = dbx.files_list_folder(folder_path)
    files.extend(result.entries)
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        files.extend(result.entries)
    return files

def download_file(file_path):
    _, res = dbx.files_download(file_path)
    return res.content

def gpt_summary(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "以下の内容を要約・解析してください。重複や不要部分は除外してください。"},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.strip()

def notify_line(message):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
    except Exception as e:
        print("LINE通知失敗:", e)

def find_duplicates_and_process(folder_path=MONITOR_FOLDER_PATH):
    files = list_files(folder_path)
    hash_map = {}
    summary_log = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            # 重複ファイルの削除
            dbx.files_delete_v2(path)
            summary_log.append(f"❌ 重複削除: {path}")
        else:
            hash_map[hash_value] = path
            try:
                text = content.decode("utf-8", errors="ignore")
                summary = gpt_summary(text)
                summary_log.append(f"📁 {file.name}\n{summary}")
            except Exception as e:
                summary_log.append(f"⚠️ {file.name} は解析できませんでした: {e}")

    # 通知送信（1000字以上は分割する）
    full_message = "\n\n".join(summary_log)
    chunks = [full_message[i:i+900] for i in range(0, len(full_message), 900)]
    for chunk in chunks:
        notify_line(chunk)

@app.route("/webhook", methods=["POST"])
def webhook():
    event_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{event_time}] Dropbox webhook 受信")
    try:
        find_duplicates_and_process()
        return "OK", 200
    except Exception as e:
        notify_line(f"解析エラー発生: {e}")
        return "Error", 500

@app.route("/", methods=["GET"])
def health_check():
    return "Slot Data Analyzer is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)