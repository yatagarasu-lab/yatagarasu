import os
import hashlib
import dropbox
from flask import Flask, request
from openai import OpenAI
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# Dropbox 認証
DROPBOX_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

# OpenAI API 認証
openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# LINE BOT 認証
line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
USER_ID = os.environ.get("LINE_USER_ID")

# 監視対象フォルダ
FOLDER_PATH = "/Apps/slot-data-analyzer"

# ファイルのハッシュを取得して重複を判定
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# Dropboxからファイル一覧取得
def list_files(folder_path=FOLDER_PATH):
    result = dbx.files_list_folder(folder_path)
    return result.entries

# Dropboxからファイルのバイナリを取得
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# GPTで解析（画像 or テキストの判定付き）
def analyze_file(filename, content):
    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        print(f"🖼 画像ファイル解析: {filename}")
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "これはスロットのスランプグラフ画像です。画像から設定傾向を簡潔に要約してください。"},
                {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{content.decode('latin1')}"}}]},
            ],
            max_tokens=500,
        )
        return result.choices[0].message.content
    else:
        print(f"📄 テキストファイル解析: {filename}")
        result = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "これはスロット設定に関するデータです。重要なポイントを簡潔に要約してください。"},
                {"role": "user", "content": content.decode("utf-8", errors="ignore")},
            ],
            max_tokens=500,
        )
        return result.choices[0].message.content

# 重複チェック用マップ
hash_map = {}

# ファイル解析と通知処理本体
def process_new_files():
    files = list_files()
    for file in files:
        path = file.path_display
        print(f"📂 新規ファイル検出: {path}")
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出 → スキップ: {path}")
            continue
        else:
            hash_map[hash_value] = path
            try:
                summary = analyze_file(file.name, content)
                print(f"🧠 解析完了: {summary}")
                line_bot_api.push_message(USER_ID, TextSendMessage(text=summary))
                print(f"📬 LINE通知送信済み ✅")
            except Exception as e:
                print(f"❌ 処理エラー: {e}")

# Webhookエンドポイント
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return challenge or "Missing challenge", 200

    if request.method == "POST":
        print("✅ Dropbox Webhook POST received!")
        process_new_files()
        return "", 200

# 起動確認用（任意）
@app.route("/")
def home():
    return "✅ Slot Data Analyzer running."