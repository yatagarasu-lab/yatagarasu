from flask import Flask, request, abort
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.exceptions import InvalidSignatureError
import dropbox
import os
import hashlib

# === Flask（フラスク：Python製のWebアプリ用フレームワーク） ===
app = Flask(__name__)

# === LINE設定 ===
channel_secret = os.environ.get("LINE_CHANNEL_SECRET")
channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
user_id = os.environ.get("LINE_USER_ID")  # 通知先ユーザーのID

if channel_secret is None or channel_access_token is None:
    print("LINEの設定が見つかりません。")
    exit(1)

handler = WebhookHandler(channel_secret)

configuration = Configuration(access_token=channel_access_token)
line_api = MessagingApi(ApiClient(configuration))

# === Dropbox設定 ===
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# === 重複ファイルチェック用 ===
def file_hash(content):
    return hashlib.md5(content).hexdigest()

def list_files(folder_path):
    response = dbx.files_list_folder(folder_path)
    return response.entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    duplicates = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            # 重複が見つかったら削除
            dbx.files_delete_v2(path)
            duplicates.append(path)
        else:
            hash_map[hash_value] = path
    return duplicates

# === Webhookルート（Dropbox確認用）===
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox が URL を確認する時の challenge 応答
        challenge = request.args.get("challenge")
        return challenge, 200
    elif request.method == "POST":
        # Dropboxから通知が来た時に処理する場所
        print("📦 Dropbox Webhook 受信")
        try:
            duplicates = find_duplicates("/Apps/slot-data-analyzer")
            if duplicates:
                message = f"重複ファイルを削除しました：\n" + "\n".join(duplicates)
            else:
                message = "Dropboxの更新を検知しました。重複はありませんでした。"
            # LINEへ通知
            line_api.push_message(
                to=user_id,
                messages=[TextMessage(text=message)]
            )
        except Exception as e:
            print(f"エラー: {e}")
        return "OK", 200

# === LINE用コールバックルート ===
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# === LINEのメッセージ受信処理 ===
@handler.add(event_type="message")
def handle_message(event):
    try:
        message = TextMessage(text="ありがとうございます")
        reply = ReplyMessageRequest(reply_token=event.reply_token, messages=[message])
        line_api.reply_message(reply)
    except Exception as e:
        print(f"返信エラー: {e}")