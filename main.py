from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import os
import dropbox
import hashlib
from openai import OpenAI
from dotenv import load_dotenv
import datetime

# 環境変数読み込み
load_dotenv()

# LINE設定
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
BASE_FOLDER = "/Apps/slot-data-analyzer"

# GPTクライアント設定
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Flaskアプリ初期化
app = Flask(__name__)

# ファイルのSHA-256ハッシュ生成
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# Dropbox内のファイル一覧取得
def list_files(folder_path):
    try:
        return dbx.files_list_folder(folder_path).entries
    except:
        return []

# Dropboxへ保存
def save_to_dropbox(file_path, content):
    dbx.files_upload(content, file_path, mode=dropbox.files.WriteMode.overwrite)

# ファイルダウンロード
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# 重複チェック
def is_duplicate(content, folder_path):
    content_hash = file_hash(content)
    for file in list_files(folder_path):
        existing = download_file(file.path_display)
        if file_hash(existing) == content_hash:
            return True, file.name
    return False, None

# GPTで要約
def analyze_file(content):
    try:
        text = content.decode("utf-8", errors="ignore")
    except Exception:
        text = "[バイナリデータ]"
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "ファイル内容を要約し、スロット、ロト、プログラミング等のカテゴリに分類してください。"},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.strip()

# カテゴリ推定（キーワード判定）
def detect_category(text):
    keywords = {
        "slot": ["スロット", "パチスロ", "設定", "差枚"],
        "lotto": ["ミニロト", "ロト", "抽選", "宝くじ"],
        "program": ["Python", "コード", "エラー", "API", "Flask"],
    }
    for category, keys in keywords.items():
        if any(key in text for key in keys):
            return category
    return "misc"

# フォルダ自動生成
def ensure_folder_exists(folder_path):
    try:
        dbx.files_get_metadata(folder_path)
    except dropbox.exceptions.ApiError:
        dbx.files_create_folder_v2(folder_path)

# Webhookエンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# テキストメッセージ処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text.encode("utf-8")
    summary = analyze_file(text)
    category = detect_category(summary)
    folder = f"{BASE_FOLDER}/{category}"
    ensure_folder_exists(folder)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = f"{folder}/{timestamp}.txt"

    duplicate, _ = is_duplicate(text, folder)
    if duplicate:
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text="✅重複テキストのためスキップしました"))
        return

    save_to_dropbox(path, text)
    line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"📄要約:\n{summary}"))

# 画像メッセージ処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = b"".join(chunk for chunk in message_content.iter_content())
    summary = analyze_file(image_data)
    category = detect_category(summary)
    folder = f"{BASE_FOLDER}/{category}"
    ensure_folder_exists(folder)
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = f"{folder}/{timestamp}.jpg"

    duplicate, _ = is_duplicate(image_data, folder)
    if duplicate:
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text="✅重複画像のためスキップしました"))
        return

    save_to_dropbox(path, image_data)
    line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"🖼️画像解析結果:\n{summary}"))

if __name__ == "__main__":
    app.run()