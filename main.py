import os
import hashlib
import tempfile
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import openai
import dropbox
from dropbox.files import WriteMode
from dotenv import load_dotenv
from PIL import Image
import pytesseract
from io import BytesIO

load_dotenv()

# 初期設定
app = Flask(__name__)
line_bot_api = LineBotApi(os.environ["LINE_CHANNEL_ACCESS_TOKEN"])
handler = WebhookHandler(os.environ["LINE_CHANNEL_SECRET"])
user_id = os.environ.get("LINE_USER_ID")  # LINE Push用
openai.api_key = os.environ["OPENAI_API_KEY"]
DROPBOX_TOKEN = os.environ["DROPBOX_ACCESS_TOKEN"]
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

# GPT解析処理
def analyze_text_with_gpt(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": text}],
            max_tokens=800
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"[GPT解析エラー] {str(e)}"

# Dropboxへアップロード
def upload_to_dropbox(filename, content):
    path = f"{DROPBOX_FOLDER}/{filename}"
    dbx.files_upload(content, path, mode=WriteMode("overwrite"))

# 重複ファイルの検出
def is_duplicate(content_bytes):
    current_hash = hashlib.sha256(content_bytes).hexdigest()
    try:
        files = dbx.files_list_folder(DROPBOX_FOLDER).entries
        for f in files:
            _, ext = os.path.splitext(f.name)
            if ext.lower() in [".txt", ".jpeg", ".jpg", ".png"]:
                md = dbx.files_download(f.path_lower)[1].content
                if hashlib.sha256(md).hexdigest() == current_hash:
                    return True
    except Exception as e:
        print(f"[重複確認エラー] {e}")
    return False

# OCR処理
def extract_text_from_image(img_bytes):
    try:
        image = Image.open(BytesIO(img_bytes))
        text = pytesseract.image_to_string(image, lang="jpn+eng")
        return text
    except Exception as e:
        return f"[OCRエラー] {str(e)}"

# LINE webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    if signature is None:
        return "NO SIGNATURE", 400

    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# LINEイベントハンドラ
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text
    content = text.encode("utf-8")
    if is_duplicate(content):
        return
    upload_to_dropbox("text_" + event.timestamp.strftime("%Y%m%d%H%M%S") + ".txt", content)
    analysis = analyze_text_with_gpt(text)
    line_bot_api.push_message(user_id, TextSendMessage(text=analysis))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    img_bytes = b"".join(chunk for chunk in message_content.iter_content())
    if is_duplicate(img_bytes):
        return
    upload_to_dropbox("image_" + event.timestamp.strftime("%Y%m%d%H%M%S") + ".jpg", img_bytes)
    ocr_text = extract_text_from_image(img_bytes)
    analysis = analyze_text_with_gpt(ocr_text)
    line_bot_api.push_message(user_id, TextSendMessage(text=analysis))

# Render用ポート設定
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)