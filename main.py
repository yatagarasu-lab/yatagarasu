import os
import hashlib
import json
import requests
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextSendMessage, MessageEvent
import dropbox
from dropbox.files import WriteMode
from PIL import Image
import pytesseract
from io import BytesIO
from datetime import datetime
import pytz

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")

DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

# Flask アプリ
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox アクセストークン取得
def get_dropbox_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# Dropboxクライアント
def get_dropbox_client():
    token = get_dropbox_access_token()
    return dropbox.Dropbox(token)

# SHA256で重複チェック
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# Dropbox内ファイル一覧
def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    res = dbx.files_list_folder(folder_path)
    return res.entries

# ダウンロード
def download_file(path):
    dbx = get_dropbox_client()
    _, res = dbx.files_download(path)
    return res.content

# 重複削除
def delete_duplicates(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            content = download_file(file.path_display)
            h = file_hash(content)

            if h in hash_map:
                dbx.files_delete_v2(file.path_display)
                print(f"✅ 重複削除: {file.name}")
            else:
                hash_map[h] = file.path_display

# OCR解析（現状は使わない）
def extract_text_from_image(image_bytes):
    image = Image.open(BytesIO(image_bytes))
    text = pytesseract.image_to_string(image, lang="jpn+eng")
    return text.strip()

# LINE通知
def send_line_message(text):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
    except Exception as e:
        print(f"❌ LINE通知失敗: {e}")

# 日本時間で夜間かどうか
def is_nighttime_japan():
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst)
    hour = now.hour
    return hour >= 22 or hour < 6

# Webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ Signatureエラー（署名不一致）")
        abort(400)
    return "OK"

# メッセージ処理
@handler.add(MessageEvent)
def handle_message(event):
    if event.message.type == "image":
        if not is_nighttime_japan():
            send_line_message("⏰ 現在は夜間処理時間外（22:00〜翌6:00）です。")
            return "OK"

        # 画像取得
        message_id = event.message.id
        content = line_bot_api.get_message_content(message_id)
        image_bytes = b''.join(chunk for chunk in content.iter_content())

        # Dropbox保存
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        dbx_path = f"/Apps/slot-data-analyzer/{filename}"
        dbx = get_dropbox_client()
        dbx.files_upload(image_bytes, dbx_path, mode=WriteMode("add"))

        # OCR無効化中
        result = "🧠 画像を受信しました（夜間のみ解析実行）"

        # LINE通知
        send_line_message(result)

        # 重複削除
        delete_duplicates("/Apps/slot-data-analyzer")
    else:
        send_line_message("📸 現在は画像のみ対応しています。")

    return "OK"

# 起動
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)