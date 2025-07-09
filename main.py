import os
import io
import time
import hashlib
import pytz
from datetime import datetime
from flask import Flask, request
import dropbox
from dropbox.files import WriteMode
from linebot import LineBotApi
from linebot.models import TextSendMessage

# OCR関連
try:
    from PIL import Image
    import easyocr
    reader = easyocr.Reader(['ja', 'en'], gpu=False)
    OCR_ENABLED = True
except:
    OCR_ENABLED = False

# 初期設定
app = Flask(__name__)
dbx = dropbox.Dropbox(oauth2_refresh_token=os.environ['DROPBOX_REFRESH_TOKEN'],
                      app_key=os.environ['DROPBOX_APP_KEY'],
                      app_secret=os.environ['DROPBOX_APP_SECRET'])
line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
USER_ID = os.environ['LINE_USER_ID']

# 時間制限（22:00〜翌6:00 JST）
def is_nighttime():
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst).time()
    return now >= datetime.strptime("22:00", "%H:%M").time() or now <= datetime.strptime("06:00", "%H:%M").time()

# ハッシュ生成（重複検出＋ユニーク名用）
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# OCR解析（画像のみ）
def run_ocr(file_bytes):
    if not OCR_ENABLED:
        return "OCR未対応（easyocr未インストール）"
    try:
        image = Image.open(io.BytesIO(file_bytes))
        result = reader.readtext(image)
        text = "\n".join([item[1] for item in result])
        return text if text.strip() else "テキストが検出されませんでした"
    except Exception as e:
        return f"OCRエラー: {str(e)}"

# ファイル保存
def save_to_dropbox(file_bytes, filename, subfolder):
    # ファイルハッシュ確認
    hash_val = file_hash(file_bytes)
    base_folder = "/slot-data-analyzer"
    folder = f"{base_folder}/{subfolder}"

    # Dropboxの全ファイルを取得し重複確認
    try:
        entries = dbx.files_list_folder(folder).entries
        for entry in entries:
            _, ext = os.path.splitext(entry.name)
            if isinstance(entry, dropbox.files.FileMetadata):
                existing = dbx.files_download(entry.path_display)[1].content
                if file_hash(existing) == hash_val:
                    dbx.files_delete_v2(entry.path_display)
    except dropbox.exceptions.ApiError:
        dbx.files_create_folder_v2(folder)

    # ファイル名をユニークにして保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name, ext = os.path.splitext(filename)
    unique_name = f"{name}_{timestamp}_{hash_val[:6]}{ext}"
    path = f"{folder}/{unique_name}"

    dbx.files_upload(file_bytes, path, mode=WriteMode("overwrite"))
    return unique_name

# Webhook受信
@app.route("/webhook", methods=["POST"])
def webhook():
    if not is_nighttime():
        return "🕒 日中のため処理スキップ", 200

    try:
        data = request.get_json()
        for entry in data['list_folder']['entries']:
            if entry['.tag'] == 'file':
                path = entry['path_display']
                metadata, res = dbx.files_download(path)
                content = res.content
                filename = os.path.basename(path)
                ext = os.path.splitext(filename)[1].lower()

                if ext in ['.jpg', '.jpeg', '.png']:
                    saved_name = save_to_dropbox(content, filename, "images")
                    ocr_result = run_ocr(content)
                    message = f"📸 新しい画像ファイルを受信しました：\n{saved_name}\n\n📝 OCR結果：\n{ocr_result}"
                elif ext in ['.mp4', '.mov']:
                    saved_name = save_to_dropbox(content, filename, "videos")
                    message = f"🎞️ 新しい動画ファイルを受信しました：\n{saved_name}\n※動画解析は現在準備中です"
                else:
                    saved_name = save_to_dropbox(content, filename, "others")
                    message = f"📁 未対応ファイルを保存しました：{saved_name}"

                line_bot_api.push_message(USER_ID, TextSendMessage(text=message))
        return "✅ 処理完了", 200

    except Exception as e:
        error_message = f"❌ 処理エラー: {str(e)}"
        try:
            line_bot_api.push_message(USER_ID, TextSendMessage(text=error_message))
        except:
            pass
        return error_message, 500

@app.route("/", methods=["GET"])
def home():
    return "🏠 Slot Data Analyzer v3.0 (夜間自動解析対応)"