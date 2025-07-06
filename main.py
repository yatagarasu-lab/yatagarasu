import os
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import dropbox
from openai import OpenAI
from analyze_file import analyze_file  # 独自のファイル解析スクリプト
from line_push import send_line_message  # LINE通知用関数
from hash_util import is_duplicate, save_hash  # ✅ 重複チェック機能を追加

# --- 各種キー ---
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
USER_ID = os.environ.get("LINE_USER_ID")

# --- 初期化 ---
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai = OpenAI(api_key=OPENAI_API_KEY)

# --- Flask アプリ ---
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "OK"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# --- 画像受信イベント処理 ---
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)

    file_data = b"".join(chunk for chunk in message_content.iter_content(chunk_size=1024))

    # ✅ 重複チェック
    if is_duplicate(file_data):
        send_line_message("⚠️ この画像はすでに処理済みです。")
        return
    save_hash(file_data)

    file_hash_val = hashlib.md5(file_data).hexdigest()
    filename = f"{file_hash_val}.jpg"
    dropbox_path = f"/Apps/slot-data-analyzer/{filename}"

    # Dropboxにアップロード
    dbx.files_upload(file_data, dropbox_path, mode=dropbox.files.WriteMode.overwrite)

    # ローカル保存 → 解析
    local_path = f"/tmp/{filename}"
    with open(local_path, "wb") as f:
        f.write(file_data)

    result = analyze_file(local_path)
    send_line_message(f"✅ 解析完了: {filename}\n\n{result[:300]}...")

# --- テキスト受信イベント処理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    received_text = event.message.text
    send_line_message(f"ありがとうございます。受信した内容：{received_text}")

# --- 起動 ---
if __name__ == "__main__":
    app.run()