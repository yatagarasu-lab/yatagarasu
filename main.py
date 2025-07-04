import os
import json
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import dropbox
from openai import OpenAI

# 環境変数
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
DROPBOX_ACCESS_TOKEN = os.environ["DROPBOX_ACCESS_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
LINE_USER_ID = os.environ["LINE_USER_ID"]

# クライアント初期化（proxies引数を削除）
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

app = Flask(__name__)

def save_to_dropbox(filename, content):
    dbx.files_upload(content.encode(), f"/Apps/slot-data-analyzer/{filename}", mode=dropbox.files.WriteMode.overwrite)
    print(f"[Dropbox] 保存: {filename}")

def notify_line(text):
    from linebot.models import TextSendMessage
    message = TextSendMessage(text=text)
    line_bot_api.push_message(LINE_USER_ID, messages=message)
    print(f"[LINE] 通知送信: {text}")

def summarize_with_gpt(content):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "これはDropboxから取得されたファイルの内容です。重複を省きつつ、簡潔に要約してください。"},
            {"role": "user", "content": content}
        ],
        max_tokens=1000,
    )
    summary = response.choices[0].message.content
    print("[GPT] 要約結果取得")
    return summary

def file_hash(content):
    return hashlib.md5(content.encode()).hexdigest()

def is_duplicate(new_hash, known_hashes):
    return new_hash in known_hashes

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text
    filename = f"{event.timestamp}_text.txt"
    content_hash = file_hash(text)

    existing_files = dbx.files_list_folder("/Apps/slot-data-analyzer").entries
    known_hashes = set()
    for file in existing_files:
        _, res = dbx.files_download(file.path_display)
        file_content = res.content.decode()
        known_hashes.add(file_hash(file_content))

    if is_duplicate(content_hash, known_hashes):
        print("[重複] 同一内容のファイルあり → 保存スキップ")
        return

    save_to_dropbox(filename, text)
    summary = summarize_with_gpt(text)
    notify_line(f"✅ 新規テキスト保存・要約:\n{summary}")

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    image_content = line_bot_api.get_message_content(message_id)
    filename = f"{event.timestamp}_image.jpg"
    data = image_content.content
    hash_val = hashlib.md5(data).hexdigest()

    existing_files = dbx.files_list_folder("/Apps/slot-data-analyzer").entries
    known_hashes = set()
    for file in existing_files:
        metadata, res = dbx.files_download(file.path_display)
        known_hashes.add(hashlib.md5(res.content).hexdigest())

    if is_duplicate(hash_val, known_hashes):
        print("[重複] 同一画像あり → 保存スキップ")
        return

    dbx.files_upload(data, f"/Apps/slot-data-analyzer/{filename}", mode=dropbox.files.WriteMode.overwrite)
    print(f"[Dropbox] 画像保存: {filename}")
    notify_line("🖼️ 新しい画像をDropboxに保存しました")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)