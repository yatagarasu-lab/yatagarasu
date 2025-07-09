import os
import io
import json
import hashlib
import pytz
import datetime
import dropbox
import requests
import openai
import easyocr
import numpy as np
from PIL import Image
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from dotenv import load_dotenv
from tqdm import tqdm

# 環境変数の読み込み
load_dotenv()

# LINEとOpenAIのAPIキー設定
line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(os.environ['LINE_CHANNEL_SECRET'])
openai.api_key = os.environ['OPENAI_API_KEY']
DROPBOX_ACCESS_TOKEN = os.environ['DROPBOX_REFRESH_TOKEN']
DROPBOX_PATH = "/Apps/slot-data-analyzer"
USER_ID = os.environ.get("LINE_USER_ID")

# Dropbox接続
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# EasyOCRリーダー初期化（日本語）
ocr_reader = easyocr.Reader(['ja', 'en'], gpu=False)

# Flaskサーバー
app = Flask(__name__)

# 日本時間の夜間帯かどうか
def is_nighttime_japan():
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.datetime.now(jst)
    return 22 <= now.hour or now.hour < 6

# ファイルのハッシュを取得
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# Dropbox内のファイル一覧取得
def list_files(folder_path=DROPBOX_PATH):
    try:
        res = dbx.files_list_folder(folder_path)
        return res.entries
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox API error: {e}")
        return []

# Dropboxファイルをダウンロード
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# GPT解析関数（画像・テキスト）
def analyze_file(content, filename):
    result = ""
    if filename.endswith((".jpg", ".jpeg", ".png")):
        image = Image.open(io.BytesIO(content)).convert("RGB")
        img_array = np.array(image)
        ocr_result = ocr_reader.readtext(img_array, detail=0)
        prompt = f"この画像のOCR文字列:\n{ocr_result}\n\nこれがスロットの設定示唆や挙動であれば、その内容を分析してください。"
        print("OCR文字列:", ocr_result)
    elif filename.endswith(".txt"):
        prompt = content.decode("utf-8")
    else:
        prompt = "このファイルの内容を解説してください。"

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたはスロット設定分析の専門家です。"},
            {"role": "user", "content": prompt}
        ]
    )
    result = response.choices[0].message['content']
    return result

# LINEに通知送信
def send_line_message(text):
    if USER_ID:
        line_bot_api.push_message(USER_ID, TextSendMessage(text=text))

# 重複ファイル検出＆削除
def remove_duplicates():
    files = list_files()
    hash_map = {}
    for f in tqdm(files):
        path = f.path_display
        content = download_file(path)
        h = file_hash(content)
        if h in hash_map:
            dbx.files_delete_v2(path)
            print(f"重複削除: {path}")
        else:
            hash_map[h] = path

# DropboxのWebhook受信
@app.route("/dropbox-webhook", methods=["POST"])
def dropbox_webhook():
    if not is_nighttime_japan():
        return "日中のためスキップ", 200

    for f in list_files():
        path = f.path_display
        content = download_file(path)
        result = analyze_file(content, path)
        send_line_message(f"[解析結果] {os.path.basename(path)}\n{result}")

    remove_duplicates()
    return "OK", 200

# LINEからの受信処理
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    img_content = line_bot_api.get_message_content(message_id).content
    filename = f"{datetime.datetime.now().timestamp()}.jpg"
    dbx.files_upload(img_content, f"{DROPBOX_PATH}/{filename}")
    send_line_message("画像をDropboxに保存しました（夜間に解析されます）")

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text
    filename = f"{datetime.datetime.now().timestamp()}.txt"
    dbx.files_upload(text.encode(), f"{DROPBOX_PATH}/{filename}")
    send_line_message("テキストをDropboxに保存しました（夜間に解析されます）")

@app.route("/", methods=["GET"])
def health_check():
    return "LINE × Dropbox × GPT Ready"

# アプリ起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)