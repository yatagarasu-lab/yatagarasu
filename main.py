import os
import hashlib
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    MessagingApiClient,
    Configuration,
    ApiClient,
    ReplyMessageRequest,
    TextMessage,
    PushMessageRequest
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent
)
import dropbox

# === 設定 ===
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")  # LINE通知先
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")

# === Flask 初期化 ===
app = Flask(__name__)

# === LINE初期化 ===
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
line_bot_api = MessagingApiClient(configuration)

# === Dropbox 初期化 ===
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

# === ファイル保存関数 ===
def save_to_dropbox(filename, data):
    path = f"/Apps/slot-data-analyzer/{filename}"
    dbx.files_upload(data, path, mode=dropbox.files.WriteMode("overwrite"))

# === 重複ファイルチェック ===
def file_hash(data):
    return hashlib.md5(data).hexdigest()

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = dbx.files_list_folder(folder_path).entries
    hash_map = {}

    for file in files:
        path = file.path_display
        _, res = dbx.files_download(path)
        content = res.content
        hash_value = file_hash(content)

        if hash_value in hash_map:
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

# === GPT処理（ダミー） ===
def analyze_file_with_gpt(filename, content):
    # ここでGPTによる解析ロジックを挿入する
    return f"{filename} を解析しました。"

# === Webhook エンドポイント ===
@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        abort(400)
    return "OK"

# === イベントハンドラ ===
@handler.add(MessageEvent)
def handle_message(event):
    message = event.message

    if isinstance(message, TextMessageContent):
        text = message.text.encode("utf-8")
        filename = f"text_{event.timestamp}.txt"
        save_to_dropbox(filename, text)
        find_duplicates()

        result = analyze_file_with_gpt(filename, text)

    elif isinstance(message, ImageMessageContent):
        message_content = line_bot_api.get_message_content(message.id)
        data = b"".join(chunk for chunk in message_content.iter_content(chunk_size=1024))
        filename = f"image_{event.timestamp}.jpg"
        save_to_dropbox(filename, data)
        find_duplicates()

        result = analyze_file_with_gpt(filename, data)

    else:
        result = "対応していないファイル形式です。"

    # LINEへ返信
    line_bot_api.push_message(
        PushMessageRequest(
            to=USER_ID,
            messages=[TextMessage(text="ありがとうございます")]
        )
    )

# === Flaskアプリ起動 ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)