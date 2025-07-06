import os
import hashlib
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
import dropbox
from openai import OpenAI

app = Flask(__name__)

# 環境変数
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
DROPBOX_ACCESS_TOKEN = os.environ.get('DROPBOX_ACCESS_TOKEN')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
LINE_USER_ID = os.environ.get('LINE_USER_ID')

# LINE Bot 設定
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox クライアント
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# OpenAI クライアント
client = OpenAI(api_key=OPENAI_API_KEY)

@app.route('/')
def home():
    return 'Dropbox × LINE × GPT 完全自動連携システム 起動中'

# Dropbox Webhook 用エンドポイント
@app.route('/dropbox-webhook', methods=['GET', 'POST'])
def dropbox_webhook():
    if request.method == 'GET':
        return request.args.get('challenge')
    elif request.method == 'POST':
        process_dropbox_files()
        return '', 200
    else:
        abort(400)

def list_files(folder_path="/Apps/slot-data-analyzer"):
    result = dbx.files_list_folder(folder_path)
    return result.entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def is_duplicate(new_content, existing_files):
    new_hash = file_hash(new_content)
    for file in existing_files:
        if file_hash(download_file(file.path_display)) == new_hash:
            return file
    return None

def process_dropbox_files():
    folder_path = "/Apps/slot-data-analyzer"
    files = list_files(folder_path)
    existing = {file.path_display: download_file(file.path_display) for file in files}

    for file in files:
        path = file.path_display
        content = existing[path]

        duplicate = is_duplicate(content, files)
        if duplicate and duplicate.path_display != path:
            dbx.files_delete_v2(path)
            notify_line(f"重複ファイルを削除しました:\n{path}")
            continue

        try:
            result = analyze_with_gpt(content)
            notify_line(f"📦ファイル解析完了: {path}\n\n📝解析結果:\n{result}")
        except Exception as e:
            notify_line(f"❌解析エラー: {e}")

def analyze_with_gpt(content):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "これはDropboxに保存されたファイルの内容です。重要な情報を要約し、スロットやパチンコの設定・傾向・特徴を中心に分析してください。"},
            {"role": "user", "content": content.decode("utf-8", errors="ignore")}
        ]
    )
    return response.choices[0].message.content.strip()

def notify_line(message):
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))

# Dropbox OAuth2 Callback（リフレッシュトークン取得）
@app.route('/oauth2/callback')
def oauth2_callback():
    code = request.args.get('code')
    if not code:
        return '認証コードが見つかりませんでした。'

    token_url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': os.environ['DROPBOX_APP_KEY'],
        'client_secret': os.environ['DROPBOX_APP_SECRET'],
        'redirect_uri': 'https://slot-data-analyzer.onrender.com/oauth2/callback'
    }

    response = requests.post(token_url, data=data)
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens.get('access_token')
        refresh_token = tokens.get('refresh_token')
        return f"✅ アクセストークン: {access_token}<br>🔄 リフレッシュトークン: {refresh_token}"
    else:
        return f"❌ トークン取得失敗: {response.text}"

# LINE Webhook エンドポイント（メッセージ受付）
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        abort(400)
    return 'OK'

if __name__ == "__main__":
    app.run()