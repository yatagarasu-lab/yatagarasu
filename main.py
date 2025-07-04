import os
import hashlib
import dropbox
import openai
from flask import Flask, request, jsonify
from linebot import LineBotApi
from linebot.models import TextSendMessage
from PIL import Image
from io import BytesIO

# --- 各種設定 ---
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"

# --- 初期化 ---
app = Flask(__name__)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# --- 重複ファイルのハッシュ比較 ---
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# --- ファイルをすべて取得 ---
def list_files(folder_path):
    files = []
    result = dbx.files_list_folder(folder_path)
    files.extend(result.entries)
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        files.extend(result.entries)
    return files

# --- ファイルをダウンロード ---
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# --- GPT解析処理（画像＆テキスト両対応） ---
def analyze_file(file_path):
    content = download_file(file_path)
    file_ext = file_path.lower().split(".")[-1]

    if file_ext in ["jpg", "jpeg", "png", "gif"]:
        image = BytesIO(content)
        response = openai.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": "この画像を要約・分析してください。"},
                    {"type": "image_url", "image_url": {"url": f"data:image/{file_ext};base64,{content.hex()}", "detail": "low"}}
                ]
            }],
            max_tokens=1000
        )
        return response.choices[0].message.content

    else:
        text = content.decode("utf-8", errors="ignore")
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": f"次のファイル内容を要約・分析してください:\n{text}"}],
            max_tokens=1000
        )
        return response.choices[0].message.content

# --- LINE通知 ---
def notify_line(text):
    message = TextSendMessage(text=text)
    line_bot_api.push_message(LINE_USER_ID, message)

# --- Webhookエンドポイント（Dropbox変更通知） ---
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge", "")
    elif request.method == "POST":
        folder_path = "/Apps/slot-data-analyzer"
        files = list_files(folder_path)
        hash_map = {}
        new_files = []

        for file in files:
            path = file.path_display
            content = download_file(path)
            hash_value = file_hash(content)

            if hash_value in hash_map:
                dbx.files_delete_v2(path)
            else:
                hash_map[hash_value] = path
                new_files.append(path)

        for file_path in new_files:
            try:
                summary = analyze_file(file_path)
                notify_line(f"📂新ファイル: {file_path}\n📊解析結果:\n{summary}")
            except Exception as e:
                notify_line(f"❌解析エラー（{file_path}）: {str(e)}")

        return "OK", 200

# --- 起動設定（Render用）---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)