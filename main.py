from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import os
import dropbox
import gzip
from io import BytesIO

from gpt_utils import process_with_gpt
from dropbox_handler import list_files, download_file, file_hash, delete_file

# Flaskアプリ初期化
app = Flask(__name__)

# 環境変数から取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")

# LINE bot・Dropbox 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# --- 重複ファイル削除処理 ---
def find_and_remove_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """Dropbox内の重複ファイルを検出・削除"""
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            delete_file(path)
        else:
            hash_map[hash_value] = path

# --- ルート確認用 ---
@app.route("/", methods=["GET"])
def health_check():
    return "LINE-Dropbox GPT Bot is running", 200

# --- Dropbox Webhook ---
@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge"), 200
    if request.method == "POST":
        # 通知を受けたら重複チェックを実行
        find_and_remove_duplicates()
        return "OK", 200

# --- LINE Webhook 受信 ---
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# --- テキストメッセージ処理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text

    # gzip圧縮
    compressed = BytesIO()
    with gzip.GzipFile(fileobj=compressed, mode="wb") as f:
        f.write(text.encode())
    compressed.seek(0)

    # Dropbox保存
    filename = f"{user_id}_{event.timestamp}.txt.gz"
    dbx.files_upload(compressed.read(), f"/スロットデータ/{filename}")

    # GPT処理（元テキスト使用）
    gpt_result = process_with_gpt(text)

    # LINE返信（固定）
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text="ありがとうございます")
    )

# --- 画像メッセージ処理 ---
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    message_id = event.message.id

    # 画像取得
    image_content = line_bot_api.get_message_content(message_id).content
    filename = f"{user_id}_{message_id}.jpg"

    # Dropbox保存
    dbx.files_upload(image_content, f"/スロットデータ/{filename}")

    # GPT処理（未実装）
    # process_with_gpt_image(image_content)

    # LINE返信（固定）
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text="ありがとうございます")
    )