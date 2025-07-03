import os
import json
import hashlib
from flask import Flask, request
import dropbox
import openai
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# === APIキー類 ===
DROPBOX_TOKEN = os.environ['DROPBOX_ACCESS_TOKEN']
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_USER_ID = os.environ['LINE_USER_ID']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

# === インスタンス生成 ===
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

# === ハッシュ比較で重複検出 ===
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# === Dropboxのファイル一覧取得 ===
def list_files(folder="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder)
    return res.entries

# === ファイルをダウンロード ===
def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

# === GPTで要約生成（記憶ベース対応） ===
def summarize_content(content, filename=""):
    try:
        text = content.decode('utf-8', errors='ignore')
    except:
        text = "（画像またはバイナリデータ）"

    prompt = f"次の内容を日本語で要約してください。\n\n【ファイル名】{filename}\n\n{text}\n\nまた、これまでのやり取りや記憶ベースで補足説明がある場合は追記してください。"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# === ファイル保存先フォルダを指定して保存 ===
def save_summary_to_dropbox(summary, filename):
    path = f"/Apps/slot-data-analyzer/要約/{filename}.txt"
    dbx.files_upload(summary.encode("utf-8"), path, mode=dropbox.files.WriteMode("overwrite"))

# === LINE通知送信 ===
def notify_line(text):
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))

# === Webhookエンドポイント ===
@app.route("/webhook", methods=["POST"])
def webhook():
    folder_path = "/Apps/slot-data-analyzer"
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            dbx.files_delete_v2(path)  # 重複なら削除
            continue
        else:
            hash_map[hash_value] = path
            summary = summarize_content(content, filename=file.name)
            save_summary_to_dropbox(summary, file.name)
            notify_line(f"🧠 新しいファイル「{file.name}」を要約してDropboxに保存しました。")

    return "OK", 200

# === Renderトップページ対応 ===
@app.route("/")
def index():
    return "✅ GPT自動記録 & Dropbox連携中", 200