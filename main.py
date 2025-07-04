from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage

import os
import hashlib
import dropbox
from datetime import datetime
from openai import OpenAI

# 環境変数取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
DROPBOX_SAVE_PATH = "/Apps/slot-data-analyzer"

# 初期化
app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai = OpenAI(api_key=OPENAI_API_KEY)

# ハッシュで重複確認
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def is_duplicate(content):
    files = dbx.files_list_folder(DROPBOX_SAVE_PATH).entries
    hash_value = file_hash(content)
    for f in files:
        meta, res = dbx.files_download(f.path_display)
        if file_hash(res.content) == hash_value:
            return True
    return False

# Dropboxに保存
def save_to_dropbox(filename, content):
    path = f"{DROPBOX_SAVE_PATH}/{filename}"
    dbx.files_upload(content, path, mode=dropbox.files.WriteMode("overwrite"))
    return path

# GPT要約
def gpt_summarize(content):
    try:
        result = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "この内容を簡潔に要約してください。"},
                {"role": "user", "content": content.decode("utf-8", errors="ignore")},
            ],
            max_tokens=300
        )
        return result.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT処理エラー: {str(e)}"

# 画像処理
def handle_image(event):
    message_id = event.message.id
    content = line_bot_api.get_message_content(message_id)
    image_data = b''.join(chunk for chunk in content.iter_content())

    if is_duplicate(image_data):
        return "重複ファイルとしてスキップされました。"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"image_{timestamp}.jpg"
    save_to_dropbox(filename, image_data)

    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=f"画像をDropboxに保存しました: {filename}"))
    return "保存完了"

# テキスト処理
def handle_text(event):
    text = event.message.text
    content = text.encode('utf-8')

    if is_duplicate(content):
        return "重複テキストとしてスキップされました。"

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"text_{timestamp}.txt"
    save_to_dropbox(filename, content)

    # GPTで要約
    summary = gpt_summarize(content)
    message = f"📝テキスト保存: {filename}\n\n🧠要約:\n{summary}"
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))

    return "保存＆要約完了"

# LINE Webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# メッセージ処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    handle_text(event)

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    handle_image(event)

# Dropbox Webhook確認
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge"), 200
    if request.method == "POST":
        print("Dropbox Webhook POST受信（自動処理）")
        return "OK", 200
    return "Method Not Allowed", 405

# 動作確認
@app.route("/", methods=["GET"])
def home():
    return "LINE & Dropbox BOT + GPT連携 稼働中", 200