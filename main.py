import os
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import dropbox
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# LINE APIの初期化
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Dropbox APIの初期化
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

app = Flask(__name__)

# ファイルのハッシュ値を計算して重複判定に使用
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# Dropboxからファイルをダウンロード
def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

# Dropboxフォルダ内のファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    result = dbx.files_list_folder(folder_path)
    return result.entries

# 重複ファイルの確認と削除
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

# LINEからのWebhookリクエスト受信
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    if "確認" in text or "チェック" in text:
        find_duplicates()
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text="Dropbox内の重複ファイルを整理しました。"))
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

# アプリの起動
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)