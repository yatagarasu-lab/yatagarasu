import os
import json
import hashlib
from flask import Flask, request
from linebot import LineBotApi
from linebot.models import TextSendMessage
import openai
import dropbox

app = Flask(__name__)

# LINE設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# OpenAI設定
openai.api_key = os.environ["OPENAI_API_KEY"]

# Dropbox設定
DROPBOX_APP_KEY = os.environ["DROPBOX_APP_KEY"]
DROPBOX_APP_SECRET = os.environ["DROPBOX_APP_SECRET"]
DROPBOX_REFRESH_TOKEN = os.environ["DROPBOX_REFRESH_TOKEN"]
dbx = dropbox.Dropbox(oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
                      app_key=DROPBOX_APP_KEY,
                      app_secret=DROPBOX_APP_SECRET)

# Dropbox内の対象フォルダ
TARGET_FOLDER = "/Apps/slot-data-analyzer"

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def list_files(folder_path):
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content.decode("utf-8", errors="ignore")

def summarize_with_gpt(text):
    prompt = f"次の内容を要約してください：\n\n{text}\n\n--- 要約:"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT要約エラー] {e}"

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.json
        if "list_folder" in data.get("delta", {}):
            changed_paths = [entry.get("path_display") for entry in list_files(TARGET_FOLDER)]

            hash_map = {}
            latest_summary = ""

            for path in changed_paths:
                content = download_file(path)
                h = file_hash(content.encode("utf-8"))
                if h in hash_map:
                    # 重複ファイル → 削除
                    dbx.files_delete_v2(path)
                else:
                    hash_map[h] = path
                    # GPTで要約
                    summary = summarize_with_gpt(content)
                    latest_summary += f"📄 {os.path.basename(path)}:\n{summary}\n\n"

            if latest_summary:
                line_bot_api.push_message(
                    LINE_USER_ID,
                    TextSendMessage(text=latest_summary[:5000])
                )
        return "OK", 200

    except Exception as e:
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=f"[Webhookエラー]\n{e}")
        )
        return "ERROR", 500

@app.route("/", methods=["GET"])
def root():
    return "Dropbox + GPT + LINE Bot is working!", 200