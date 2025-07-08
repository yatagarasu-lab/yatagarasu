import os
import hashlib
import json
import dropbox
import openai
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent
)

# ----------------- 認証情報 -----------------
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ----------------- 初期設定 -----------------
openai.api_key = OPENAI_API_KEY
app = Flask(__name__)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

# Dropboxクライアント
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

# ----------------- GPT解析 -----------------
def analyze_file_content(content: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下のデータを要約・分析し、スロット設定の傾向や注意点を簡潔に教えてください。"},
                {"role": "user", "content": content}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"[GPT解析エラー] {str(e)}"

# ----------------- ファイル保存処理 -----------------
def save_file_to_dropbox(file_name, content):
    path = f"/Apps/slot-data-analyzer/{file_name}"
    dbx.files_upload(content, path, mode=dropbox.files.WriteMode.overwrite)
    return path

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def is_duplicate(content):
    try:
        hash_map = {}
        files = dbx.files_list_folder("/Apps/slot-data-analyzer").entries
        for f in files:
            if isinstance(f, dropbox.files.FileMetadata):
                existing = dbx.files_download(f.path_display)[1].content
                h = file_hash(existing)
                if h in hash_map:
                    continue
                hash_map[h] = f.path_display
                if file_hash(content) == h:
                    return True
        return False
    except Exception as e:
        print("重複チェック失敗:", str(e))
        return False

# ----------------- Webhookルート -----------------
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# ----------------- メッセージイベント処理 -----------------
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    text = event.message.text
    reply_text = "ありがとうございます"
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(LINE_USER_ID, [
            TextMessage(text=reply_text)
        ])

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    message_id = event.message.id
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        content = line_bot_api.get_message_content(message_id)
        binary = b"".join(content.iter_content(chunk_size=1024))
        if is_duplicate(binary):
            reply = "同じ画像は既に保存済みです。"
        else:
            file_name = f"{message_id}.jpg"
            save_file_to_dropbox(file_name, binary)
            reply = f"画像を保存しました: {file_name}"
        line_bot_api.push_message(LINE_USER_ID, [
            TextMessage(text=reply)
        ])

# ----------------- アプリ起動（Render用） -----------------
if __name__ == "__main__":
    app.run()