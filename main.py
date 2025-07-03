from flask import Flask, request
import os
import hashlib
import requests
import dropbox

app = Flask(__name__)

# LINE設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

# LINE通知関数
def send_line_message(message):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)
    print(f"LINE送信ステータス: {response.status_code}, 応答: {response.text}")

# Dropboxファイル一覧取得
def list_files(path):
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    files = dbx.files_list_folder(path).entries
    return [f for f in files if isinstance(f, dropbox.files.FileMetadata)]

# Dropboxファイル取得
def download_file(path):
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    _, res = dbx.files_download(path)
    return res.content

# 重複チェック用ハッシュ
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# 重複ファイルチェック＆通知
def check_and_notify_duplicates():
    files = list_files(DROPBOX_FOLDER)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            msg = f"⚠️ 重複ファイル検出\n{path}\n（同一: {hash_map[hash_value]}）"
            send_line_message(msg)
            print(msg)
            # dbx.files_delete_v2(path)  # ←削除したい場合は有効化
        else:
            hash_map[hash_value] = path
            msg = f"✅ 新規ファイル：{os.path.basename(path)}"
            send_line_message(msg)
            print(msg)

# Webhook受信
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge")

    print("✅ Dropbox Webhook Received")
    check_and_notify_duplicates()
    return "OK", 200

# Render実行用
if __name__ == "__main__":
    app.run(debug=True)