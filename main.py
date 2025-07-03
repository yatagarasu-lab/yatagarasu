import os
import hashlib
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import dropbox
from dropbox.files import WriteMode
import requests

# === 初期化 ===
app = Flask(__name__)
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# === ユーティリティ関数 ===
def file_hash(data):
    return hashlib.md5(data).hexdigest()

def upload_to_dropbox(file_content, filename, subfolder="slot-data-analyzer"):
    path = f"/{subfolder}/{filename}"
    dbx.files_upload(file_content, path, mode=WriteMode("overwrite"))

def list_files(folder="/slot-data-analyzer"):
    return dbx.files_list_folder(folder).entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def analyze_with_gpt(content):
    text = content.decode(errors="ignore")[:1000]
    return f"（GPT要約）内容冒頭: {text[:50]}..."

def generate_knowledge_summary():
    knowledge = '''
【スロット設定知識まとめ - 最新】
・川崎エリア：ガイア川崎は新台導入数日後に設定投入傾向あり
・ピーアーク新城：6/25に東京喰種、北斗、ジャグラーに設定
・PIA系列：マギレコと東京喰種は合同機種対象で扱い良し
・1000カス対応店：朝カス・1000カスなどの示唆情報は重要
・来店演者「じゅりそん」：Dステ立川では北斗、かぐやに設定履歴あり
'''.strip()
    return knowledge.encode("utf-8")

def export_knowledge_to_dropbox():
    content = generate_knowledge_summary()
    filename = f"knowledge_{datetime.now().strftime('%Y%m%d')}.txt"
    path = f"/slot-knowledge-export/{filename}"
    dbx.files_upload(content, path, mode=WriteMode("overwrite"))

# === LINE処理 ===
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text
    filename = f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    upload_to_dropbox(text.encode("utf-8"), filename)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id).content
    filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    upload_to_dropbox(image_content, filename)
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

# === Dropbox Webhook（通知受信） ===
@app.route("/webhook", methods=["GET"])
def webhook_verify():
    return request.args.get("challenge")

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        files = list_files()
        hash_map = {}
        results = []

        for file in files:
            path = file.path_display
            content = download_file(path)
            hash_value = file_hash(content)

            if hash_value in hash_map:
                dbx.files_delete_v2(path)
                continue
            else:
                hash_map[hash_value] = path
                summary = analyze_with_gpt(content)
                results.append(f"📄 {file.name}\\n{summary}")

        # 知識まとめもエクスポート
        export_knowledge_to_dropbox()

        message = "\\n\\n".join(results) if results else "⚠️ 新規ファイルはありませんでした。"
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
        return "OK"
    except Exception as e:
        print("❌ Webhook処理エラー:", e)
        return "NG", 500

# === 起動確認用 ===
@app.route("/")
def home():
    return "✅ GPT + LINE + Dropbox サーバー起動中"