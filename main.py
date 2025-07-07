from flask import Flask, request, abort
import os
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from dropbox_utils import find_duplicates

app = Flask(__name__)

# === LINE設定 ===
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# === Dropbox Webhookエンドポイント ===
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox webhook確認
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        print("📩 DropboxからWebhook受信")
        try:
            body = request.get_data(as_text=True)
            print("🔍 Payload:", body)

            # 重複チェック
            find_duplicates()

            # LINE通知
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text="📁 Dropboxにファイルが追加または更新されました（重複チェック済）")
            )
            return '', 200
        except Exception as e:
            print("❌ Webhook処理中にエラー:", e)
            return 'Error', 500

# === LINE BotのWebhookエンドポイント ===
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# === LINEメッセージイベント（手動テスト用） ===
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text
    reply = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# === Flask起動 ===
if __name__ == "__main__":
    app.run()