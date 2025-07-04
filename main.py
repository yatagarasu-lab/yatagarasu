import os
import hashlib
import dropbox
from flask import Flask, request
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from linebot.exceptions import InvalidSignatureError
import openai

# .envの読み込み
load_dotenv()

# 環境変数の取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

PORT = int(os.getenv("PORT", 10000))

# LINE Bot の初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox の初期化
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

# Flask アプリケーションの初期化
app = Flask(__name__)

# ファイルの SHA-256 ハッシュ計算
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# Dropbox からファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

# ファイルの内容を取得
def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

# 重複ファイルの検出と削除（オプション）
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # dbx.files_delete_v2(path)  # ← 本当に削除するならアンコメント
        else:
            hash_map[hash_value] = path

# LINE Webhookエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK", 200

# メッセージ受信時の処理
@handler.add(event=__import__('linebot.models').linebot.models.events.MessageEvent)
def handle_message(event):
    if event.source.user_id != LINE_USER_ID:
        return  # 応答しない（認証）

    # 確認用のシンプルな返信
    message_text = event.message.text
    reply_text = f"受信しました：{message_text}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# アプリの起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)