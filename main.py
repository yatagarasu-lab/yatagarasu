from flask import Flask, request, jsonify
import os
import dropbox
import hashlib
from io import BytesIO
from PIL import Image
import base64
import openai
import requests

app = Flask(__name__)

# 環境変数の読み込み
DROPBOX_REFRESH_TOKEN = os.environ["DROPBOX_REFRESH_TOKEN"]
DROPBOX_CLIENT_ID = os.environ["DROPBOX_CLIENT_ID"]
DROPBOX_CLIENT_SECRET = os.environ["DROPBOX_CLIENT_SECRET"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_USER_ID = os.environ["LINE_USER_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
GAS_WEBHOOK_URL = os.environ["GAS_WEBHOOK_URL"]

# OpenAI 初期化
openai.api_key = OPENAI_API_KEY

# Dropbox アクセストークン取得
def get_access_token():
    token_url = "https://api.dropbox.com/oauth2/token"
    payload = {
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "grant_type": "refresh_token",
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET,
    }
    response = requests.post(token_url, data=payload)
    return response.json().get("access_token")

# Dropboxファイル一覧取得
def list_files():
    dbx = dropbox.Dropbox(get_access_token())
    result = dbx.files_list_folder(path="", recursive=True)
    return result.entries

# ファイル内容ダウンロード
def download_file(path):
    dbx = dropbox.Dropbox(get_access_token())
    metadata, res = dbx.files_download(path)
    return res.content

# ファイルのハッシュ生成（重複判定用）
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# 重複ファイル検出＆削除
def find_duplicates(files):
    hash_map = {}
    duplicates = []
    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            content = download_file(file.path_display)
            hash_val = file_hash(content)
            if hash_val in hash_map:
                duplicates.append(file.path_display)
            else:
                hash_map[hash_val] = file.path_display
    return duplicates

# GPTで要約処理（画像・テキスト両対応）
def summarize_file(file_path):
    content = download_file(file_path)
    if file_path.lower().endswith((".jpg", ".jpeg", ".png")):
        base64_img = base64.b64encode(content).decode("utf-8")
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}},
                    {"type": "text", "text": "この画像を要約してください。"}
                ]}
            ]
        )
        return response.choices[0].message.content
    else:
        text = content.decode("utf-8", errors="ignore")
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f"以下を要約してください:\n{text}"}
            ]
        )
        return response.choices[0].message.content

# LINEに通知
def send_line_notify(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, json=payload)

# GASへ送信
def send_to_spreadsheet(source, message):
    payload = {
        "source": source,
        "message": message
    }
    try:
        response = requests.post(GAS_WEBHOOK_URL, json=payload)
        print(f"📤 GAS送信結果: {response.text}")
    except Exception as e:
        print(f"❌ GAS送信エラー: {e}")

# Webhookエンドポイント
@app.route("/", methods=["POST"])
def webhook():
    print("✅ Webhook受信")
    files = list_files()
    duplicates = find_duplicates(files)

    for file in files:
        if isinstance(file, dropbox.files.FileMetadata) and file.path_display not in duplicates:
            summary = summarize_file(file.path_display)
            file_name = os.path.basename(file.path_display)
            message = f"📄ファイル: {file_name}\n📝要約: {summary}"
            send_line_notify(message)
            send_to_spreadsheet(file_name, summary)

    # 重複削除
    if duplicates:
        dbx = dropbox.Dropbox(get_access_token())
        for dup in duplicates:
            dbx.files_delete_v2(dup)
            print(f"🗑️ 重複削除: {dup}")

    return jsonify({"status": "success"})

# 動作確認用
@app.route("/", methods=["GET"])
def index():
    return "📡 Yatagarasu GPT Automation is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)