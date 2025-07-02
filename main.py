from flask import Flask, request, jsonify
import dropbox
import os
from utils import is_duplicate, analyze_file, notify_line

app = Flask(__name__)

DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN")
DROPBOX_FOLDER = "/スロットデータ"
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox Webhook検証用 (challenge)
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        # Webhookが通知されたらファイルをスキャン
        entries = dbx.files_list_folder(DROPBOX_FOLDER, recursive=True).entries
        for entry in entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                _, ext = os.path.splitext(entry.name)
                if ext.lower() in [".txt", ".csv", ".xlsx", ".json", ".jpg", ".jpeg", ".png"]:
                    _, res = dbx.files_download(entry.path_display)
                    content = res.content

                    if is_duplicate(content):
                        dbx.files_delete_v2(entry.path_display)
                    else:
                        result = analyze_file(content, entry.name)
                        notify_line(f"✅新規ファイル解析結果\n📄{entry.name}\n\n{result}")
        return "OK", 200
        import hashlib
import os
import openai
import base64
import requests

# すでに処理済みのハッシュを一時的に保存（本番はDB推奨）
processed_hashes = set()

# ファイルの重複チェック
def is_duplicate(content: bytes) -> bool:
    file_hash = hashlib.sha256(content).hexdigest()
    if file_hash in processed_hashes:
        return True
    processed_hashes.add(file_hash)
    return False

# OpenAI でファイル解析
def analyze_file(content: bytes, filename: str) -> str:
    openai.api_key = os.getenv("OPENAI_API_KEY")
    try:
        b64 = base64.b64encode(content).decode("utf-8")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはデータ解析アシスタントです。アップロードされたファイルを読み取り、その内容を要約・解説してください。"},
                {"role": "user", "content": f"ファイル名: {filename}\n以下のBase64形式のデータを解析してください:\n{b64}"}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"❌解析エラー: {e}"

# LINE通知（LINE Notify使用）
def notify_line(message: str):
    token = os.getenv("LINE_NOTIFY_TOKEN")
    if not token:
        print("LINE通知トークンが未設定です")
        return
    url = "https://notify-api.line.me/api/notify"
    headers = {"Authorization": f"Bearer {token}"}
    data = {"message": message}
    try:
        requests.post(url, headers=headers, data=data)
    except Exception as e:
        print(f"LINE通知失敗: {e}")