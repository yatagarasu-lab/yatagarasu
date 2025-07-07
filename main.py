from flask import Flask, request, abort
import os
import json
import dropbox
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dropbox_utils import list_files, download_file, find_duplicates

app = Flask(__name__)

# LINEチャンネル設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox設定（リフレッシュトークン方式）
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
WATCH_FOLDER_PATH = "/Apps/slot-data-analyzer"

# Dropboxインスタンス作成
dbx = dropbox.Dropbox(
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET,
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
)

# DropboxのWebhook（検証 or 通知）
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge"), 200

    if request.method == "POST":
        print("📩 DropboxからWebhook通知を受信")

        try:
            payload = request.get_data(as_text=True)
            print(f"🔍 通知内容: {payload}")

            # 重複ファイルの確認と通知
            find_duplicates(WATCH_FOLDER_PATH)

            # LINEへPush通知送信
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text="📦 Dropboxに新しいファイルが追加されました")
            )
            return "", 200
        except Exception as e:
            print(f"❌ Webhook処理エラー: {e}")
            return "Error", 500

# LINE Botのメッセージ受信
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# LINEからのテキストメッセージ応答（ありがとう固定返信）
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

if __name__ == "__main__":
    app.run()