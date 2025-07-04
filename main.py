from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage
from openai import OpenAI
import dropbox
import os
import hashlib
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# 各種APIキーなど環境変数から取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_USER_ID = os.getenv("LINE_USER_ID")  # ユーザーID固定

# Flaskアプリ初期化
app = Flask(__name__)

# LINE API初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox API初期化
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# OpenAI SDK v1.30.1対応クライアント初期化
client = OpenAI(api_key=OPENAI_API_KEY)

# ファイルのハッシュ取得（重複チェック用）
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# Dropboxからファイル一覧取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

# Dropboxからファイルをダウンロード
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# 重複ファイルチェックと削除（同一内容のファイルは削除）
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

# GPTで内容要約（画像やテキストに応じて応答）
def analyze_with_gpt(text):
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "あなたはLINEに届いた画像や文章を解析・要約し、スロットに関する情報を整理するアシスタントです。"},
            {"role": "user", "content": text}
        ],
        max_tokens=500
    )
    return response.choices[0].message.content.strip()

# LINE Webhookエンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error: {e}")
    return 'OK'

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_text = event.message.text

    # Dropboxへ保存
    file_name = f"/Apps/slot-data-analyzer/from_line_{event.timestamp}.txt"
    dbx.files_upload(user_text.encode(), file_name)

    # GPTで解析
    gpt_summary = analyze_with_gpt(user_text)

    # LINEに送信
    line_bot_api.push_message(
        LINE_USER_ID,
        TextMessage(text=f"📝解析結果:\n{gpt_summary}")
    )

    # 重複ファイルチェック（解析後）
    find_duplicates()

# 起動コマンド
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)))