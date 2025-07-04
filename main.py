from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import os
import dropbox
import hashlib
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# LINE設定
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

# GPT設定
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# LINEユーザーID
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Flaskアプリ
app = Flask(__name__)


# ---------------------- 共通関数 ------------------------

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def save_to_dropbox(file_path, content):
    dbx.files_upload(content, file_path, mode=dropbox.files.WriteMode.overwrite)

def list_files(folder_path):
    result = dbx.files_list_folder(folder_path)
    return result.entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def is_duplicate(new_content):
    new_hash = file_hash(new_content)
    for file in list_files_recursive(DROPBOX_FOLDER):
        existing = download_file(file.path_display)
        if file_hash(existing) == new_hash:
            return True, file.name
    return False, None

def list_files_recursive(path):
    """サブフォルダも含めて再帰的にファイルを取得"""
    entries = []
    result = dbx.files_list_folder(path, recursive=True)
    entries.extend(result.entries)
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        entries.extend(result.entries)
    return [e for e in entries if isinstance(e, dropbox.files.FileMetadata)]

def analyze_file(content):
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "画像またはテキストの内容をスロットイベント、ロト情報、またはプログラミングに関する情報として要約してください。"},
            {"role": "user", "content": content.decode("utf-8", errors="ignore")}
        ]
    )
    return response.choices[0].message.content.strip()

def classify_genre(text):
    content = text.lower()
    if "北斗" in content or "差枚" in content or "スロット" in content or "設定" in content:
        return "スロット"
    elif "ロト" in content or "ミニロト" in content or "当せん" in content:
        return "ロト"
    elif "python" in content or "コード" in content or "render" in content or "flask" in content:
        return "プログラミング"
    elif "政治" in content or "ニュース" in content:
        return "ニュース"
    else:
        return "その他"

def ensure_folder_exists(path):
    try:
        dbx.files_get_metadata(path)
    except dropbox.exceptions.ApiError:
        dbx.files_create_folder_v2(path)

def get_dropbox_path(genre, filename):
    date = datetime.now().strftime("%Y-%m-%d")
    folder_path = f"{DROPBOX_FOLDER}/{genre}/{date}"
    ensure_folder_exists(f"{DROPBOX_FOLDER}/{genre}")
    ensure_folder_exists(folder_path)
    return f"{folder_path}/{filename}"


# ------------------------ LINE Webhook -----------------------

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# ------------------------ テキストメッセージ処理 -----------------------

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text.encode("utf-8")
    decoded_text = text.decode("utf-8", errors="ignore")
    genre = classify_genre(decoded_text)
    filename = f"{event.timestamp}.txt"
    file_path = get_dropbox_path(genre, filename)

    duplicate, existing = is_duplicate(text)
    if not duplicate:
        save_to_dropbox(file_path, text)
        summary = analyze_file(text)
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"[{genre}]の要約:\n{summary}"))
    else:
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text="重複ファイルのためスキップしました"))


# ------------------------ 画像メッセージ処理 -----------------------

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = b"".join(chunk for chunk in message_content.iter_content())

    # 一旦テキストとしてGPTで分類（OCR的に）
    try:
        genre = classify_genre(image_data.decode("utf-8", errors="ignore"))
    except Exception:
        genre = "画像"

    filename = f"{event.timestamp}.jpg"
    file_path = get_dropbox_path(genre, filename)

    duplicate, existing = is_duplicate(image_data)
    if not duplicate:
        save_to_dropbox(file_path, image_data)
        summary = analyze_file(image_data)
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"[{genre}]画像の解析結果:\n{summary}"))
    else:
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text="重複画像のためスキップしました"))


# ------------------------ 実行 -----------------------

if __name__ == "__main__":
    app.run()