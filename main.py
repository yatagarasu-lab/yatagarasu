from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import TextMessage, MessageEvent, TextSendMessage
import os
import time
import dropbox

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# LINE設定
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Flaskアプリケーション
app = Flask(__name__)

# 通知間隔制御
last_notification_time = 0
notification_interval = 60  # 秒

@app.route("/")
def health_check():
    return "OK"

@app.route("/callback", methods=['POST'])
def callback():
    global last_notification_time

    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    app.logger.info(f"Request body: {body}")

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    # Push通知を間引く処理
    now = time.time()
    if now - last_notification_time > notification_interval:
        try:
            line_bot_api.push_message(USER_ID, TextSendMessage(text="ありがとうございます"))
            last_notification_time = now
            app.logger.info("Push通知送信成功")
        except Exception as e:
            app.logger.error(f"Push通知送信エラー: {e}")
    else:
        app.logger.info("通知スキップ（間隔内）")

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 通常のテキストメッセージの受信処理（応答不要）
    app.logger.info(f"受信メッセージ: {event.message.text}")
    return

if __name__ == "__main__":
    app.run()