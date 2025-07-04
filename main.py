from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import dropbox
import hashlib
import os
import openai
import tempfile

app = Flask(__name__)

# --- 各種APIキーと設定（環境変数に設定してある前提） ---
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"  # 固定ユーザーID

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY


# --- Dropbox ファイル操作 ---
def list_files(folder_path="/Apps/slot-data-analyzer"):
    result = dbx.files_list_folder(folder_path)
    return result.entries

def download_file(file_path):
    _, res = dbx.files_download(file_path)
    return res.content

def file_hash(content):
    return hashlib.md5(content).hexdigest()


# --- 重複ファイル検出＆削除 ---
def clean_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    deleted_files = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        h = file_hash(content)
        if h in hash_map:
            dbx.files_delete_v2(path)
            deleted_files.append(path)
        else:
            hash_map[h] = path

    return deleted_files


# --- GPTによるファイル解析 ---
def analyze_file_with_gpt(file_path):
    content = download_file(file_path).decode("utf-8", errors="ignore")
    prompt = f"このデータの内容を要約してください:\n\n{content[:3000]}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )
    return response.choices[0].message["content"]


# --- Dropbox Webhookエンドポイント ---
@app.route("/webhook", methods=["POST"])
def webhook():
    # Dropbox からの通知処理
    folder_path = "/Apps/slot-data-analyzer"
    deleted = clean_duplicates(folder_path)
    files = list_files(folder_path)
    messages = []

    for file in files:
        file_path = file.path_display
        summary = analyze_file_with_gpt(file_path)
        messages.append(f"📄 {file.name}\n{summary}")

    if deleted:
        messages.append(f"🧹 重複削除: {len(deleted)}件")

    final_message = "\n\n".join(messages)
    if final_message:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=final_message[:5000]))

    return "OK"


# --- LINEメッセージ受信エンドポイント ---
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


# --- LINEメッセージ受信時の処理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 受信テキストをDropboxに保存
    text = event.message.text
    filename = f"text_{event.timestamp}.txt"
    dbx.files_upload(text.encode("utf-8"), f"/Apps/slot-data-analyzer/{filename}")
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))


if __name__ == "__main__":
    app.run()