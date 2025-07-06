import os
import json
import hashlib
from flask import Flask, request, abort
import openai
import dropbox
from linebot import LineBotApi
from linebot.models import TextSendMessage

# Flask アプリ作成
app = Flask(__name__)

# LINE API 初期設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Dropbox 初期設定（リフレッシュトークン対応）
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")

def get_dropbox_client():
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox
    from dropbox.files import WriteMode

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect, DropboxOAuth2Flow
    from dropbox import DropboxOAuth2FlowResult
    from dropbox.oauth import DropboxOAuth2Flow
    from dropbox import Dropbox

    from dropbox.oauth import DropboxOAuth2Flow, OAuth2FlowNoRedirectResult
    from dropbox import DropboxOAuth2FlowResult

    from dropbox import DropboxOAuth2FlowNoRedirect

    from dropbox import Dropbox, DropboxOAuth2FlowNoRedirect
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox

    from dropbox.oauth import DropboxOAuth2FlowNoRedirect

    from dropbox import Dropbox, DropboxOAuth2FlowNoRedirect

    dbx = dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )
    return dbx

# 重複判定のためのハッシュ生成
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# ファイル一覧取得
def list_files(folder_path):
    dbx = get_dropbox_client()
    res = dbx.files_list_folder(folder_path)
    return res.entries

# ファイル取得
def download_file(path):
    dbx = get_dropbox_client()
    metadata, res = dbx.files_download(path)
    return res.content

# GPTで内容要約
def summarize_with_gpt(content):
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "これはDropboxから取得したテキストや画像内容の要約です。"},
            {"role": "user", "content": content.decode("utf-8", errors="ignore")}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# ルート確認用
@app.route("/")
def home():
    return "Hello from Flask"

# Dropbox Webhook
@app.route("/dropbox-webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge")

    if request.method == "POST":
        print("🔔 Dropbox Webhook Triggered")

        folder_path = "/Apps/slot-data-analyzer"
        dbx = get_dropbox_client()
        files = list_files(folder_path)

        hash_map = {}
        summaries = []

        for file in files:
            path = file.path_display
            content = download_file(path)
            hash_value = file_hash(content)

            if hash_value in hash_map:
                print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
                # 重複削除する場合はこちらを有効化
                # dbx.files_delete_v2(path)
                continue
            else:
                hash_map[hash_value] = path
                summary = summarize_with_gpt(content)
                summaries.append(f"📄 {file.name} の要約:\n{summary}")

        if summaries:
            summary_text = "\n\n".join(summaries)
        else:
            summary_text = "新しいファイルはありませんでした。"

        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=summary_text)
        )

        return "OK"

    return abort(400)