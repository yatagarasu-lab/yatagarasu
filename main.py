import os
import hashlib
import dropbox
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from openai import OpenAI
from dotenv import load_dotenv
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox.exceptions import AuthError

# 環境変数をロード
load_dotenv()

# Flaskアプリの初期化
app = Flask(__name__)

# 環境変数の取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LINE Bot初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAI初期化
client = OpenAI(api_key=OPENAI_API_KEY)

# Dropboxへの接続
def get_dropbox_client():
    try:
        from dropbox.oauth import DropboxOAuth2FlowNoRedirect
        from dropbox import Dropbox, DropboxOAuth2Flow
        from dropbox.oauth import OAuth2FlowNoRedirectResult

        refresh_token = DROPBOX_REFRESH_TOKEN
        app_key = DROPBOX_APP_KEY
        app_secret = DROPBOX_APP_SECRET

        dbx = dropbox.Dropbox(
            app_key=app_key,
            app_secret=app_secret,
            oauth2_refresh_token=refresh_token
        )
        dbx.users_get_current_account()  # 接続確認
        return dbx
    except AuthError as e:
        print(f"Dropbox認証エラー: {e}")
        return None

# Dropboxのファイル一覧取得
def list_files(folder_path):
    dbx = get_dropbox_client()
    if not dbx:
        return []
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"ファイル一覧取得エラー: {e}")
        return []

# Dropboxからファイルダウンロード
def download_file(path):
    dbx = get_dropbox_client()
    if not dbx:
        return None
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"ファイルダウンロードエラー: {e}")
        return None

# ファイルのハッシュ計算
def file_hash(data):
    return hashlib.sha256(data).hexdigest()

# 重複ファイルの検出
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    duplicates = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        if not content:
            continue
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            duplicates.append(path)
            # dbx.files_delete_v2(path)  # 必要なら有効化
        else:
            hash_map[hash_value] = path
    return duplicates

# ファイル内容の要約（OpenAI）
def summarize_text(content):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下の内容を要約してください。"},
                {"role": "user", "content": content}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"要約エラー: {e}")
        return "要約できませんでした。"

# LINE通知送信
def notify_line(message):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
    except Exception as e:
        print(f"LINE通知エラー: {e}")

# Dropbox Webhook
@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge")
    elif request.method == "POST":
        print("📦 Dropbox webhook POST 受信しました")
        process_new_files()
        return "OK"

# Dropboxファイルの解析処理
def process_new_files():
    folder = "/Apps/slot-data-analyzer"
    files = list_files(folder)
    if not files:
        notify_line("📂 新しいファイルは見つかりませんでした。")
        return

    for file in files:
        content = download_file(file.path_display)
        if content:
            try:
                text = content.decode("utf-8", errors="ignore")
                summary = summarize_text(text)
                notify_line(f"📄 {file.name} の要約:\n{summary}")
            except Exception as e:
                notify_line(f"⚠️ {file.name} の処理中にエラー: {e}")

# 動作確認用エンドポイント
@app.route("/", methods=["GET"])
def index():
    return "✅ GPT Dropbox連携サーバー稼働中"

# アプリ起動用（Render用に必要）
app = app