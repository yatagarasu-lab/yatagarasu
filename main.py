from flask import Flask, request, Response
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
import dropbox
import hashlib
import os
import io
from PIL import Image
import logging

# 環境変数から各種キーを取得（Renderに設定済みであること）
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")

# Flaskアプリの初期化
app = Flask(__name__)

# LINE API 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Dropbox API 初期化
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# 重複チェック用ハッシュマップ
hash_map = {}

def file_hash(content):
    """ファイルのSHA256ハッシュを返す"""
    return hashlib.sha256(content).hexdigest()

def is_duplicate_file(content):
    """重複ファイルかを判定する"""
    h = file_hash(content)
    if h in hash_map:
        return True
    hash_map[h] = True
    return False

def list_files(folder_path):
    """Dropbox内のファイル一覧を取得"""
    result = dbx.files_list_folder(folder_path)
    return result.entries

def download_file(path):
    """Dropboxのファイルをダウンロード"""
    metadata, res = dbx.files_download(path)
    return res.content

def summarize_image(content):
    """画像を要約（仮処理：サイズ情報を送信）"""
    image = Image.open(io.BytesIO(content))
    width, height = image.size
    return f"画像サイズ: {width}x{height}"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # Dropbox 検証用（GETでchallenge返す）
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return Response(challenge, status=200)

    # 実際のWebhook通知（POST）
    print("✅ Dropbox Webhook 受信")

    try:
        folder_path = "/Apps/slot-data-analyzer"
        files = list_files(folder_path)

        for file in files:
            if isinstance(file, dropbox.files.FileMetadata):
                path = file.path_display
                content = download_file(path)

                if is_duplicate_file(content):
                    print(f"⚠️ 重複ファイル検出: {path}")
                    continue

                summary = summarize_image(content)
                message = f"📥 新しいファイル:\n{file.name}\n{summary}"
                line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
                print(f"✅ LINE送信: {file.name}")

    except Exception as e:
        logging.exception("エラー発生")
        return Response("Internal Server Error", status=500)

    return Response("OK", status=200)

@app.route("/callback", methods=["POST"])
def callback():
    return "OK", 200

@app.route("/", methods=["GET"])
def health_check():
    return "✅ App is running.", 200