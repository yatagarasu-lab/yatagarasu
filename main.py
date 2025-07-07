from flask import Flask, request, abort
import os
import requests
import hashlib
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import dropbox

app = Flask(__name__)

# 環境変数の取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
USER_ID = os.getenv("USER_ID")

# LINE Bot SDKの初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropboxアクセストークンを取得
def get_dropbox_access_token():
    response = requests.post(
        "https://api.dropboxapi.com/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": DROPBOX_REFRESH_TOKEN
        },
        auth=(DROPBOX_APP_KEY, DROPBOX_APP_SECRET)
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("Dropbox access_token 取得失敗:", response.json())
        return None

# Dropbox接続
def get_dropbox_client():
    token = get_dropbox_access_token()
    return dropbox.Dropbox(token)

# Dropboxファイル一覧取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    result = dbx.files_list_folder(folder_path)
    return result.entries

# ファイルをダウンロード
def download_file(path):
    dbx = get_dropbox_client()
    _, res = dbx.files_download(path)
    return res.content

# ハッシュ生成で重複チェック
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# 重複ファイル削除
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    duplicates = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            duplicates.append(path)
            dbx = get_dropbox_client()
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

    return duplicates

# LINE通知送信
def send_line_message(message):
    line_bot_api.push_message(USER_ID, TextSendMessage(text=message))

# Webhook確認用
@app.route("/", methods=["GET"])
def home():
    return "Slot Data Analyzer Bot is running."

# Webhook受信
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# ユーザーメッセージ受信
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "重複チェック":
        duplicates = find_duplicates()
        if duplicates:
            message = f"重複ファイルを削除しました:\n" + "\n".join(duplicates)
        else:
            message = "重複ファイルはありませんでした。"
        send_line_message(message)
    else:
        send_line_message("ありがとうございます")