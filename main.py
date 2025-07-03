import os
import hashlib
import dropbox
from flask import Flask, request
from openai import OpenAI
from dotenv import load_dotenv

# 環境変数の読み込み（Renderでは .env 不要）
load_dotenv()

# 初期化
app = Flask(__name__)
DROPBOX_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
LINE_USER_ID = os.environ.get("LINE_USER_ID")  # 固定ユーザー通知用
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

dbx = dropbox.Dropbox(DROPBOX_TOKEN)
openai = OpenAI(api_key=OPENAI_API_KEY)

# ファイルのSHA256ハッシュ生成（重複判定用）
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# Dropboxフォルダ内のファイル一覧取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

# Dropboxファイルをダウンロード
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# GPTで要約・解析
def analyze_content(content):
    text = content.decode("utf-8", errors="ignore") if isinstance(content, bytes) else content
    prompt = f"以下のスロットデータを要約・解析してください:\n\n{text}"
    res = openai.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたはスロット専門のデータアナリストです。"},
            {"role": "user", "content": prompt}
        ]
    )
    return res.choices[0].message.content.strip()

# LINE通知送信
def send_line_message(message):
    import requests
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)
    return res.status_code

# 重複チェックと要約送信
def process_latest_file():
    folder = "/Apps/slot-data-analyzer"
    files = sorted(list_files(folder), key=lambda x: x.server_modified, reverse=True)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        h = file_hash(content)

        if h in hash_map:
            print(f"🧹 重複ファイル削除: {path}")
            dbx.files_delete_v2(path)
        else:
            hash_map[h] = path
            summary = analyze_content(content)
            send_line_message(f"📊 ファイル: {file.name}\n\n{summary}")
            break

# 📍Renderルート確認用
@app.route("/", methods=["GET"])
def home():
    return "Hello from Slot GPT Analyzer!", 200

# 📍Dropbox Webhook対応
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge", "No challenge"), 200
    elif request.method == "POST":
        print("📩 Dropbox webhook POST 受信")
        try:
            process_latest_file()
            return "OK", 200
        except Exception as e:
            print("❌ 処理失敗:", e)
            return "Error", 500

# 本番環境向け
if __name__ == "__main__":
    app.run(debug=True)