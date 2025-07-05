import os
import dropbox
import hashlib
import openai
import requests

# 環境変数から取得
DROPBOX_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

# Dropboxクライアント初期化
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
openai.api_key = OPENAI_API_KEY

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def delete_file(path):
    dbx.files_delete_v2(path)

def analyze_content_with_gpt(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "このデータを要約し、重要な特徴を簡潔に説明してください。"},
                {"role": "user", "content": content.decode("utf-8", errors="ignore")}
            ],
            temperature=0.2,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT解析エラー] {str(e)}"

def send_line_message(text):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post(url, headers=headers, json=payload)

def analyze_dropbox_updates():
    folder_path = "/Apps/slot-data-analyzer"
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            delete_file(path)
            send_line_message(f"🗑️ 重複ファイル削除: {path}")
        else:
            hash_map[hash_value] = path
            result = analyze_content_with_gpt(content)
            send_line_message(f"✅ 新規ファイル分析: {path}\n{result}")