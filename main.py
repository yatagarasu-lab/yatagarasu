from flask import Flask, request, abort
import os
import hashlib
import hmac
import json

from dropbox_utils import list_files, download_file
from gpt_utils import analyze_and_notify
from line_utils import push_message
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/")
def index():
    return "✅ サーバー稼働中", 200

# Dropbox Webhook
@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge", ""), 200

    if request.method == "POST":
        print("📩 Dropbox Webhook受信")
        try:
            data = request.get_json()
            print("📦 内容:", json.dumps(data, indent=2))

            # ファイル一覧取得して処理（Apps/slot-data-analyzer）
            entries = list_files()
            for entry in entries:
                path = entry.path_display
                content = download_file(path)
                analyze_and_notify(path, content)

            return '', 200
        except Exception as e:
            print(f"❌ Webhook処理中エラー: {e}")
            push_message("Dropboxファイル処理エラー")
            return 'Error', 500

# LINE Bot Webhook
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# LINE メッセージ返信
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    reply = "ありがとうございます"
    handler.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run()