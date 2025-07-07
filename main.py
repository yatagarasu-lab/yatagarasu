import os
import hashlib
import io
import json
import requests
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage
from linebot.exceptions import InvalidSignatureError
from dotenv import load_dotenv
from dropbox import Dropbox

# 環境変数の読み込み
load_dotenv()

# LINE API キー
LINE_CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Dropbox 認証情報
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# OpenAIキー（使ってる場合）
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Flaskアプリ初期化
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox アクセストークンの取得
def get_dropbox_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_APP_KEY,
        "client_secret": DROPBOX_APP_SECRET
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# Dropbox 初期化
def get_dropbox_client():
    access_token = get_dropbox_access_token()
    return Dropbox(access_token)

# 重複判定ハッシュ生成
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# ファイル取得と解析処理（PDF / 画像）
def analyze_file(dbx, path):
    _, res = dbx.files_download(path)
    content = res.content

    ext = os.path.splitext(path)[1].lower()
    text_result = ""

    if ext == ".pdf":
        doc = fitz.open(stream=content, filetype="pdf")
        for page in doc:
            text_result += page.get_text()
    elif ext in [".jpg", ".jpeg", ".png"]:
        image = Image.open(io.BytesIO(content))
        text_result = pytesseract.image_to_string(image)
    else:
        text_result = "[未対応のファイル形式]"

    return text_result.strip()

# ファイル一覧取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    result = dbx.files_list_folder(folder_path)
    return result.entries

# Webhook受信（LINEから）
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ファイル変更通知受信（Dropboxから）
@app.route("/dropbox_webhook", methods=["POST"])
def dropbox_webhook():
    dbx = get_dropbox_client()
    files = list_files()

    hash_map = {}

    for file in files:
        path = file.path_display
        _, res = dbx.files_download(path)
        content = res.content
        h = file_hash(content)

        if h in hash_map:
            dbx.files_delete_v2(path)
            print(f"削除: 重複 {path}")
        else:
            hash_map[h] = path
            result = analyze_file(dbx, path)
            send_line_notify(f"📥 新ファイル: {path}\n\n📄 抽出:\n{result[:500]}")

    return "OK"

# Challenge 用（GET）
@app.route("/dropbox_webhook", methods=["GET"])
def dropbox_verify():
    return request.args.get("challenge")

# LINE通知送信
def send_line_notify(text):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=text))
    except Exception as e:
        print(f"LINE通知エラー: {e}")

# ルート
@app.route("/", methods=["GET"])
def index():
    return "動作中"

# アプリ起動（ローカル用）
if __name__ == "__main__":
    app.run()