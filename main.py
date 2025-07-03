from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
import hashlib
import dropbox
import requests

# 環境変数読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

# LINE・Flask初期化
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# LINE通知関数
def send_line_message(message):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)
    print("LINE送信:", response.status_code, response.text)

# Dropboxファイル一覧と重複チェック
def list_files(folder_path="/Apps/slot-data-analyzer"):
    result = dbx.files_list_folder(folder_path)
    return [f for f in result.entries if isinstance(f, dropbox.files.FileMetadata)]

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def check_and_notify_duplicates():
    files = list_files()
    hash_map = {}
    for file in files:
        path = file.path_display
        content = download_file(path)
        h = file_hash(content)

        if h in hash_map:
            msg = f"⚠️ 重複ファイル検出: {file.name}"
            send_line_message(msg)
        else:
            hash_map[h] = path
            msg = f"✅ 新ファイル検出: {file.name}"
            send_line_message(msg)

# Dropbox Webhookエンドポイント
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge")
    elif request.method == "POST":
        print("✅ Dropbox Webhook 受信")
        check_and_notify_duplicates()
        return "", 200

# LINE Botエンドポイント（User ID取得付き）
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    print(f"✅ 取得したあなたのLINEユーザーID: {user_id}")

    # LINE返信でIDも教える（必要なら削除可）
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"あなたのLINEユーザーIDは:\n{user_id}")
    )

# アプリ起動
if __name__ == "__main__":
    app.run()