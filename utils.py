# utils.py

import os
import dropbox
import hashlib
import requests

# Dropboxからファイル内容を取得
def download_file_content(dbx, file_path):
    _, res = dbx.files_download(file_path)
    return res.content

# ファイルのハッシュを取得（重複判定用）
def get_file_hash(content):
    return hashlib.sha256(content).hexdigest()

# LINE通知（Push用）
def send_line_message(message):
    line_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    user_id = os.getenv("LINE_USER_ID")

    if not line_token or not user_id:
        print("❌ LINE環境変数が未設定")
        return

    headers = {
        "Authorization": f"Bearer {line_token}",
        "Content-Type": "application/json"
    }

    data = {
        "to": user_id,
        "messages": [{
            "type": "text",
            "text": message
        }]
    }

    response = requests.post("https://api.line.me/v2/bot/message/push", json=data, headers=headers)

    if response.status_code != 200:
        print(f"❌ LINE送信失敗: {response.text}")
    else:
        print("✅ LINE通知送信済み")