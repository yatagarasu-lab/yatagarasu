from flask import Flask, request, abort
import os
import dropbox
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from dropbox_handler import handle_dropbox_update  # ← 追加

app = Flask(__name__)

# LINEのチャンネル設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# LINEのユーザーID（Push送信用）
LINE_USER_ID = os.getenv("LINE_USER_ID")

# DropboxのWebhookエンドポイント
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox webhookの認証応答
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        print("📩 DropboxからWebhook受信")
        try:
            # Dropbox Webhook通知の受信ログ
            print("📦 処理を開始します")
            handle_dropbox_update()
            return "", 200
        except Exception as e:
            print(f"[Webhook処理エラー] {e}")
            return "Error", 500

# LINEメッセージ受信用
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("📥 LINEメッセージ受信:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# LINEメッセージイベントの応答処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    reply = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run()