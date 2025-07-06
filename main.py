import os
import hashlib
import dropbox
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage

# 環境変数取得
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 環境変数の確認（なければログ表示して終了）
if not all([DROPBOX_ACCESS_TOKEN, LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, LINE_USER_ID]):
    raise EnvironmentError("環境変数が未設定です。Renderの環境変数に設定してください。")

# 各種初期化
app = Flask(__name__)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ファイルのハッシュを計算して重複判定に使う
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# Dropboxのファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    result = dbx.files_list_folder(folder_path)
    return result.entries

# Dropboxのファイルをダウンロード
def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

# 重複ファイルを削除
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

# Webhook受信時の処理
@app.route("/webhook", methods=["POST"])
def webhook():
    find_duplicates()  # ファイル整理処理を追加
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text="ありがとうございます"))
    return "OK", 200

# Render起動用
if __name__ == "__main__":
    app.run()