from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os
from gpt_analyzer import analyze_dropbox_and_notify

app = Flask(__name__)

# 環境変数から取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)


@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """LINEで受け取ったメッセージに応じて処理を実行"""
    user_text = event.message.text.lower()
    if "解析" in user_text or "分析" in user_text:
        analyze_dropbox_and_notify()
        reply = "Dropbox内の最新データを解析しました。"
    else:
        reply = "ありがとうございます"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )


@app.route("/", methods=["GET"])
def health_check():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)