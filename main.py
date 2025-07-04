import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import dropbox
import openai
import hashlib

load_dotenv()

app = Flask(__name__)

# LINE設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
USER_ID = os.getenv("LINE_USER_ID")  # Pushメッセージ用

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

# OpenAI設定
openai.api_key = os.getenv("OPENAI_API_KEY")

def save_to_dropbox(filename, content):
    path = f"{DROPBOX_FOLDER}/{filename}"
    dbx.files_upload(content.encode(), path, mode=dropbox.files.WriteMode("overwrite"))

def file_hash(content):
    return hashlib.sha256(content.encode()).hexdigest()

def find_duplicates(folder_path=DROPBOX_FOLDER):
    files = dbx.files_list_folder(folder_path).entries
    hash_map = {}
    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            path = file.path_display
            content = dbx.files_download(path)[1].content.decode()
            hash_value = file_hash(content)
            if hash_value in hash_map:
                print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
                dbx.files_delete_v2(path)
            else:
                hash_map[hash_value] = path

def analyze_with_gpt(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "このデータを解析し、要点をまとめてください。"},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message['content']

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
def handle_message(event):
    user_text = event.message.text
    filename = f"message_{event.timestamp}.txt"

    # Dropboxに保存
    save_to_dropbox(filename, user_text)

    # 重複ファイル削除
    find_duplicates()

    # GPT解析（要約）
    result = analyze_with_gpt(user_text)

    # LINEに返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=result)
    )

@app.route("/")
def index():
    return "Service is running."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)