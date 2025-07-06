import os
import hashlib
import dropbox
from flask import Flask, request
from linebot import LineBotApi
from linebot.models import TextSendMessage

# LINE設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"

# Flask初期化
app = Flask(__name__)

# ファイルのSHA256ハッシュを取得（重複検出用）
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# Dropbox内のファイル一覧を取得
def list_files(folder_path):
    result = dbx.files_list_folder(folder_path)
    return result.entries

# ファイルをダウンロード
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# 重複ファイルを削除
def remove_duplicates():
    files = list_files(DROPBOX_FOLDER_PATH)
    hash_map = {}
    removed_files = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            dbx.files_delete_v2(path)
            removed_files.append(path)
        else:
            hash_map[hash_value] = path

    return removed_files

# LINE通知送信
def send_line_message(text):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
    except Exception as e:
        print("LINE通知エラー:", e)

# Dropbox Webhook
@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        if challenge:
            return challenge, 200
        return "Missing challenge", 400

    if request.method == "POST":
        print("✅ Dropbox Webhook POST received!")
        removed = remove_duplicates()

        if removed:
            message = f"🧹 重複ファイルを削除しました:\n" + "\n".join(removed)
        else:
            message = "🔍 重複ファイルは見つかりませんでした。"

        send_line_message(message)
        return "", 200

# LINE Bot Webhook（メッセージ受信確認用）
@app.route("/callback", methods=["POST"])
def line_callback():
    try:
        body = request.get_data(as_text=True)
        print("🔔 LINEからメッセージを受信:", body)
        return "OK", 200
    except Exception as e:
        print("LINE Webhook エラー:", e)
        return "Error", 500

# 起動確認
@app.route("/", methods=["GET"])
def home():
    return "Bot is running", 200

if __name__ == "__main__":
    app.run(debug=True)