import os
import hashlib
import dropbox
import fitz  # PyMuPDF
import pytesseract
import io
import base64
import requests
from PIL import Image
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Dropboxアクセストークンを自動取得
def get_dropbox_access_token():
    refresh_token = os.getenv('DROPBOX_REFRESH_TOKEN')
    app_key = os.getenv('DROPBOX_APP_KEY')
    app_secret = os.getenv('DROPBOX_APP_SECRET')
    url = "https://api.dropboxapi.com/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": app_key,
        "client_secret": app_secret,
    }
    response = requests.post(url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# Dropbox初期化
def create_dropbox_client():
    token = get_dropbox_access_token()
    return dropbox.Dropbox(token)

# ハッシュで重複チェック
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# ファイルの中身を抽出
def extract_text_from_file(path, dbx):
    _, res = dbx.files_download(path)
    content = res.content

    if path.endswith(".pdf"):
        text = ""
        doc = fitz.open(stream=content, filetype="pdf")
        for page in doc:
            text += page.get_text()
        return text.strip()

    elif path.endswith((".png", ".jpg", ".jpeg")):
        image = Image.open(io.BytesIO(content))
        text = pytesseract.image_to_string(image, lang="jpn")
        return text.strip()

    return None

# 重複ファイルの削除機能
def find_and_delete_duplicates(folder_path="/Apps/slot-data-analyzer"):
    dbx = create_dropbox_client()
    result = dbx.files_list_folder(folder_path)
    hash_map = {}

    for entry in result.entries:
        path = entry.path_display
        _, res = dbx.files_download(path)
        content = res.content
        h = file_hash(content)
        if h in hash_map:
            print(f"重複削除: {path}")
            dbx.files_delete_v2(path)
        else:
            hash_map[h] = path

# Flaskアプリ
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv('LINE_CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.getenv('LINE_CHANNEL_SECRET'))

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Error: {e}")
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    print(f"受信メッセージ: {event.message.text}")

    try:
        folder = "/Apps/slot-data-analyzer"
        dbx = create_dropbox_client()
        result = dbx.files_list_folder(folder)

        messages = []
        for entry in result.entries:
            content = extract_text_from_file(entry.path_display, dbx)
            if content:
                messages.append(f"{entry.name}:\n{content[:200]}...")

        final_msg = "\n\n".join(messages) if messages else "解析できるファイルが見つかりませんでした。"
        line_bot_api.push_message(user_id, TextSendMessage(text=final_msg))

    except Exception as e:
        line_bot_api.push_message(user_id, TextSendMessage(text=f"エラーが発生しました: {str(e)}"))

# 起動
if __name__ == "__main__":
    app.run()