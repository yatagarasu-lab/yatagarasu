from flask import Flask, request, abort
import os
import json
import hashlib
import hmac
import dropbox
from dropbox.files import WriteMode
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from line_utils import notify_user
from dropbox_utils import list_files, download_file, file_hash
import openai

app = Flask(__name__)

# LINE設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox設定
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

# OpenAI設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# アクセストークン取得（リフレッシュ方式）
def get_dropbox_access_token():
    import requests
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# Dropboxクライアント初期化
def get_dropbox_client():
    token = get_dropbox_access_token()
    return dropbox.Dropbox(token)

# 重複ファイルを検出して削除
def remove_duplicates(dbx, folder_path="/Apps/slot-data-analyzer"):
    files = dbx.files_list_folder(folder_path).entries
    hash_map = {}

    for file in files:
        path = file.path_display
        _, res = dbx.files_download(path)
        content = res.content
        h = file_hash(content)

        if h in hash_map:
            print(f"🗑️ 重複削除: {path}（同一: {hash_map[h]}）")
            dbx.files_delete_v2(path)
        else:
            hash_map[h] = path

# ファイルをGPTで解析して通知
def analyze_and_notify(dbx, folder_path="/Apps/slot-data-analyzer"):
    files = dbx.files_list_folder(folder_path).entries
    if not files:
        notify_user("📁 Dropboxにファイルがありません")
        return

    latest_file = sorted(files, key=lambda f: f.server_modified, reverse=True)[0]
    _, res = dbx.files_download(latest_file.path_display)
    content = res.content

    try:
        result = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "これはスロットのデータです。内容を要約し、重複がないか確認してください。"},
                {"role": "user", "content": content.decode("utf-8", errors="ignore")}
            ]
        )
        summary = result["choices"][0]["message"]["content"]
        notify_user(f"📄 最新ファイル解析:\n{summary[:1000]}")
    except Exception as e:
        notify_user(f"❌ GPT解析エラー: {e}")

# Dropbox webhook用エンドポイント
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge"), 200

    if request.method == "POST":
        print("📩 Dropbox Webhook受信")
        try:
            dbx = get_dropbox_client()
            remove_duplicates(dbx)
            analyze_and_notify(dbx)
            return '', 200
        except Exception as e:
            print(f"Webhook処理エラー: {e}")
            notify_user(f"❌ Webhookエラー: {e}")
            return 'Error', 500

# LINE callback（未使用でも残す）
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("LINEメッセージ受信:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)