from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import os
import dropbox
import hashlib
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# LINE設定
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
BASE_FOLDER = "/Apps/slot-data-analyzer"

# GPT設定
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Flask
app = Flask(__name__)

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

def is_duplicate(new_content, folder_path):
    new_hash = file_hash(new_content)
    try:
        for file in list_files(folder_path):
            existing = download_file(file.path_display)
            if file_hash(existing) == new_hash:
                return True, file.name
    except dropbox.exceptions.ApiError:
        pass  # フォルダが存在しないなど
    return False, None

def analyze_file(content):
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "これはスロット・ロト・プログラムなどの解析対象データです。要約とカテゴリ分類を行ってください。"},
            {"role": "user", "content": content.decode("utf-8", errors="ignore")}
        ]
    )
    return response.choices[0].message.content.strip()

def categorize_content(text):
    text_lower = text.lower()
    if "ジャグラー" in text or "北斗" in text or "パチスロ" in text:
        return "スロット"
    elif "ロト" in text or "ミニロト" in text or "宝くじ" in text:
        return "ロト"
    elif "python" in text_lower or "flask" in text_lower or "API" in text:
        return "プログラム"
    else:
        return "その他"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    content_bytes = text.encode("utf-8")
    category = categorize_content(text)
    folder_path = f"{BASE_FOLDER}/{category}"
    filename = f"{event.timestamp}.txt"
    dropbox_path = f"{folder_path}/{filename}"

    duplicate, _ = is_duplicate(content_bytes, folder_path)
    if not duplicate:
        save_to_dropbox(dropbox_path, content_bytes)
        summary = analyze_file(content_bytes)
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"[{category}]\n要約:\n{summary}"))
    else:
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"[{category}]\n重複ファイルのためスキップしました"))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = b"".join(chunk for chunk in message_content.iter_content())
    category = "スロット"  # 現時点では画像＝スロット画像前提（後で拡張可）
    folder_path = f"{BASE_FOLDER}/{category}"
    filename = f"{event.timestamp}.jpg"
    dropbox_path = f"{folder_path}/{filename}"

    duplicate, _ = is_duplicate(image_data, folder_path)
    if not duplicate:
        save_to_dropbox(dropbox_path, image_data)
        summary = analyze_file(image_data)
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"[{category}] 画像解析結果:\n{summary}"))
    else:
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"[{category}]\n重複画像のためスキップしました"))

if __name__ == "__main__":
    app.run()