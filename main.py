import os
import hashlib
import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import dropbox

from analyze_file import analyze_file
from line_push import send_line_message
from hash_util import is_duplicate, save_hash

# 環境変数からトークンを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

# 各種API初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Flask起動
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "OK"

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# --- Image受信処理 ---
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    message_id = event.message.id

    message_content = line_bot_api.get_message_content(message_id)
    content = message_content.content

    # 重複チェック（SHA-256）
    if is_duplicate(content):
        send_line_message(user_id, "⚠️ この画像はすでに処理されています。")
        return
    save_hash(content)

    # ファイル名生成（日付＋ハッシュ）
    now = datetime.datetime.now()
    date_folder = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    file_hash = hashlib.sha256(content).hexdigest()[:8]
    filename = f"{time_str}_{file_hash}.jpg"
    dropbox_path = f"/Apps/slot-data-analyzer/{date_folder}/{filename}"

    # Dropboxに保存
    dbx.files_upload(content, dropbox_path)

    # 一時保存（/tmp）→ 解析
    local_path = f"/tmp/{filename}"
    with open(local_path, "wb") as f:
        f.write(content)

    try:
        result = analyze_file(local_path)
        message = f"✅ 保存＆解析完了！\n📁 {dropbox_path}\n\n📊 {result[:300]}..."
    except Exception as e:
        message = f"⚠️ 解析中にエラーが発生しました。\n{e}"

    send_line_message(user_id, message)

# --- テキストメッセージ受信処理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    received_text = event.message.text
    send_line_message(user_id, f"ありがとうございます。受信内容：{received_text}")

# --- 起動 ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)