import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import dropbox
from datetime import datetime
import hashlib

# Flaskアプリ初期化
app = Flask(__name__)

# 環境変数からトークン取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

# LINE API初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox API初期化
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# ファイルの保存と重複チェック
def save_to_dropbox(text, user_id):
    folder_path = "/Apps/slot-data-analyzer"
    filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{user_id}.txt"
    file_path = f"{folder_path}/{filename}"
    content = text.encode("utf-8")

    # 重複チェック（ハッシュ）
    hash_value = hashlib.sha256(content).hexdigest()
    for entry in dbx.files_list_folder(folder_path).entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            existing_content = dbx.files_download(entry.path_lower)[1].content
            if hashlib.sha256(existing_content).hexdigest() == hash_value:
                print(f"重複データ検出：{filename}")
                return

    # 保存
    dbx.files_upload(content, file_path)
    print(f"保存完了：{filename}")

# ✅ ← このルートが必要！
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
def handle_message(event):
    user_id = event.source.user_id
    text = event.message.text

    # Dropboxに保存
    save_to_dropbox(text, user_id)

    # 応答
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

# 動作確認用
@app.route("/", methods=["GET"])
def hello():
    return "Hello, Render!"

# 起動（ローカル確認用）
if __name__ == "__main__":
    app.run()