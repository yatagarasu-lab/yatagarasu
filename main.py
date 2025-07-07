import os
import json
import hashlib
import dropbox
import openai
import tempfile
from flask import Flask, request
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# 環境変数からキーを取得
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# クライアント初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

# Dropboxアクセストークン取得（リフレッシュトークン対応）
def get_dropbox_client():
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox

    from dropbox.oauth import DropboxOAuth2Flow
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox.oauth import DropboxOAuth2Flow
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox.oauth import OAuth2FlowNoRedirectResult
    from dropbox.oauth import DropboxOAuth2Flow

    from dropbox.oauth import DropboxOAuth2Flow
    from dropbox.oauth import OAuth2FlowNoRedirectResult
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox.oauth import DropboxOAuth2Flow

    from dropbox import DropboxOAuth2FlowNoRedirect, Dropbox

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect, DropboxOAuth2Flow
    from dropbox.oauth import OAuth2FlowNoRedirectResult

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect, Dropbox

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect, DropboxOAuth2Flow
    from dropbox.oauth import OAuth2FlowNoRedirectResult
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect, Dropbox
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect, Dropbox

    return dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )

# ファイルハッシュで重複チェック
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# GPTでファイル内容を要約
def analyze_file(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "これはスロットの設定情報か実戦データです。内容を要約し、重要な設定示唆や傾向があれば指摘してください。"},
                {"role": "user", "content": content.decode("utf-8", errors="ignore")}
            ],
            max_tokens=800
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"[GPT解析エラー] {str(e)}"

# LINE通知
def send_line_message(text):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
    except Exception as e:
        print(f"LINE通知エラー: {e}")

# Webhookエンドポイント
@app.route("/dropbox-webhook", methods=["POST"])
def dropbox_webhook():
    dbx = get_dropbox_client()
    folder_path = "/Apps/slot-data-analyzer"
    processed_hashes = set()

    try:
        res = dbx.files_list_folder(folder_path)
        for entry in res.entries:
            path = entry.path_display
            _, ext = os.path.splitext(path)
            if ext.lower() not in [".txt", ".csv", ".log", ".json", ".md", ".jpeg", ".jpg", ".png", ".gif"]:
                continue

            md, res = dbx.files_download(path)
            content = res.content
            h = file_hash(content)
            if h in processed_hashes:
                continue
            processed_hashes.add(h)

            summary = analyze_file(content)
            send_line_message(f"🧠解析結果（{os.path.basename(path)}）\n\n{summary}")

    except Exception as e:
        print(f"Dropbox処理エラー: {e}")
        send_line_message(f"[エラー発生] {e}")

    return "OK", 200

# Webhook認証確認用
@app.route("/dropbox-webhook", methods=["GET"])
def verify():
    return request.args.get("challenge"), 200

# サーバー起動
@app.route("/")
def home():
    return "Slot Data Analyzer Bot is running!"

if __name__ == "__main__":
    app.run(debug=True)