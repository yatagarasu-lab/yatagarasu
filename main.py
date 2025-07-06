import os
import hashlib
import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import dropbox

# --- 環境変数から取得 ---
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

# --- 初期化 ---
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

app = Flask(__name__)
uploaded_hashes = set()  # メモリ内で重複管理（簡易）

# --- ヘルスチェック ---
@app.route("/", methods=["GET"])
def health():
    return "OK"

# --- LINE Webhook受信 ---
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# --- 画像受信処理 ---
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    message_id = event.message.id

    # ファイルデータ取得
    message_content = line_bot_api.get_message_content(message_id)
    content = message_content.content

    # ハッシュで重複判定
    file_hash = hashlib.sha256(content).hexdigest()
    if file_hash in uploaded_hashes:
        line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 同じ画像はすでに保存されています。"))
        return
    uploaded_hashes.add(file_hash)

    # 日付情報を取得してパス作成
    now = datetime.datetime.now()
    date_path = now.strftime("%Y/%m/%d")
    time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{time_str}_{file_hash[:8]}.jpg"
    dropbox_path = f"/Apps/slot-data-analyzer/{date_path}/{filename}"

    # Dropboxにアップロード
    dbx.files_upload(content, dropbox_path)

    # LINEへ返信
    response = f"✅ 画像をDropboxに保存しました！\n\n📁 {dropbox_path}"
    line_bot_api.push_message(user_id, TextSendMessage(text=response))

# --- テキスト受信処理 ---
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    line_bot_api.push_message(user_id, TextSendMessage(text="ありがとうございます"))

# --- サーバー起動 ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)