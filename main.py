import os
import hashlib
import dropbox
import openai
import requests
from flask import Flask, request, abort

app = Flask(__name__)

# 環境変数
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 初期化
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY


# Dropboxのファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path, recursive=True)
    return res.entries


# ファイルをダウンロードしてハッシュ取得
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content


def file_hash(content):
    return hashlib.md5(content).hexdigest()


# GPTによる解析（テキストファイル想定）
def analyze_with_gpt(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"要約: GPT解析エラー: {str(e)}"


# LINE通知送信
def send_line_message(text):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text}]
    }
    response = requests.post("https://api.line.me/v2/bot/message/push", json=data, headers=headers)
    return response.status_code


# Dropbox Webhookエンドポイント（URLチェック用）
@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        print("✅ Dropbox webhook received")
        handle_dropbox_update()
        return '', 200

    return abort(400)


# Dropbox更新時の処理
def handle_dropbox_update():
    folder_path = "/Apps/slot-data-analyzer"
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            dbx.files_delete_v2(path)
            print(f"🗑️ 重複ファイル削除: {path}")
        else:
            hash_map[hash_value] = path
            try:
                if file.name.endswith(".txt"):
                    text = content.decode("utf-8")
                    result = analyze_with_gpt(text)
                    send_line_message(f"📝 {file.name}:\n{result}")
                else:
                    send_line_message(f"📁 新規ファイル: {file.name} を受信しました")
            except Exception as e:
                send_line_message(f"⚠️ 処理エラー: {str(e)}")


# 動作確認用エンドポイント
@app.route("/")
def home():
    return "✅ GPT × Dropbox Bot is running", 200


if __name__ == "__main__":
    app.run(debug=True)