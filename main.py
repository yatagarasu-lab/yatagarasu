from flask import Flask, request, make_response
import os
import dropbox
import requests
import hashlib
import base64
import time

app = Flask(__name__)

# 環境変数
DROPBOX_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')
LINE_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# 重複判定用（記憶するハッシュ値）
processed_hashes = set()

# GPTで要約
def summarize_text(text):
    res = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4",
            "messages": [
                {"role": "system", "content": "以下の文章を要約してください。"},
                {"role": "user", "content": text}
            ],
            "max_tokens": 300
        }
    )
    return res.json()["choices"][0]["message"]["content"].strip()

# LINE通知
def notify_line(message):
    headers = {
        "Authorization": f"Bearer {LINE_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)

# Dropboxからファイル一覧を取得・内容取得・LINE送信
def handle_dropbox_check():
    dbx = dropbox.Dropbox(DROPBOX_TOKEN)
    result = dbx.files_list_folder(path="", limit=5)

    for entry in result.entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            file_path = entry.path_display
            _, res = dbx.files_download(file_path)
            content = res.content.decode(errors="ignore")

            # 重複判定（ハッシュ）
            file_hash = hashlib.sha256(content.encode()).hexdigest()
            if file_hash in processed_hashes:
                print(f"⚠️ 重複ファイルスキップ: {file_path}")
                continue
            processed_hashes.add(file_hash)

            # GPTで要約
            summary = summarize_text(content)

            # LINE通知
            notify_line(f"📄 新ファイル: {entry.name}\n🧠 要約:\n{summary}")
            time.sleep(1)  # 連投対策

# Webhook検証（GET）
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        challenge = request.args.get('challenge')
        response = make_response(challenge, 200)
        response.headers['Content-Type'] = 'text/plain'
        return response
    elif request.method == 'POST':
        print("✅ Webhook POST受信")
        handle_dropbox_check()
        return '', 200

# 定時監視用エンドポイント（/cron-check）
@app.route('/cron-check', methods=['GET'])
def cron_check():
    print("🕒 定時チェック開始")
    handle_dropbox_check()
    return 'OK', 200

# トップ確認
@app.route('/')
def index():
    return '✅ Dropbox + GPT + LINE 自動通知システム起動中'

# Render起動用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))