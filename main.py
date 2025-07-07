import os
import hashlib
import io
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from flask import Flask, request
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import TextSendMessage
import dropbox
import openai

load_dotenv()

app = Flask(__name__)

# 環境変数
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 初期化
openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def get_dropbox_client():
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox import Dropbox
    from dropbox.oauth import OAuth2Session

    refresh_token = DROPBOX_REFRESH_TOKEN
    app_key = DROPBOX_APP_KEY
    app_secret = DROPBOX_APP_SECRET

    oauth_session = OAuth2Session(
        consumer_key=app_key,
        consumer_secret=app_secret,
        token={"refresh_token": refresh_token}
    )
    dbx = Dropbox(oauth2_access_token=oauth_session.refresh_access_token()["access_token"])
    return dbx

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def download_file(dbx, path):
    _, res = dbx.files_download(path)
    return res.content

def extract_text_from_image(content):
    image = Image.open(io.BytesIO(content))
    text = pytesseract.image_to_string(image, lang='jpn+eng')
    return text

def extract_text_from_pdf(content):
    text = ""
    with fitz.open(stream=content, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def analyze_with_gpt(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "これはDropboxから抽出したデータです。要点を簡潔にまとめてください。"},
            {"role": "user", "content": text}
        ]
    )
    return response["choices"][0]["message"]["content"]

def send_line_notification(message):
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))

def is_duplicate(content, hash_map):
    h = file_hash(content)
    if h in hash_map:
        return True
    hash_map[h] = True
    return False

@app.route("/webhook", methods=["POST"])
def webhook():
    dbx = get_dropbox_client()
    folder = "/Apps/slot-data-analyzer"
    hash_map = {}

    result_message = "📦【Dropbox更新解析】\n"

    for entry in dbx.files_list_folder(folder).entries:
        path = entry.path_display
        if not isinstance(entry, dropbox.files.FileMetadata):
            continue

        content = download_file(dbx, path)

        # 重複チェック
        if is_duplicate(content, hash_map):
            dbx.files_delete_v2(path)
            continue

        if path.lower().endswith((".jpg", ".jpeg", ".png")):
            text = extract_text_from_image(content)
        elif path.lower().endswith(".pdf"):
            text = extract_text_from_pdf(content)
        else:
            continue

        summary = analyze_with_gpt(text)
        result_message += f"\n📄 {os.path.basename(path)}:\n{summary}\n"

    send_line_notification(result_message.strip())
    return "OK", 200

if __name__ == "__main__":
    app.run()