import os
import sys
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import openai
import requests
from io import BytesIO

# 環境変数の取得
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
openai.api_key = os.getenv("OPENAI_API_KEY")

if not channel_secret or not channel_access_token:
    print("環境変数が未設定です。")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)
app = Flask(__name__)

# 最後の送信時刻
last_message_time = {}

# 5分後に返信する関数
def delayed_thanks(user_id):
    time.sleep(300)  # 5分待機
    now = datetime.now()
    if (user_id in last_message_time and 
        datetime.now() - last_message_time[user_id] >= timedelta(minutes=5)):
        line_bot_api.push_message(user_id, TextSendMessage(text="ありがとうございます"))

# テキストと画像の内容をGPTに送信する関数
def analyze_with_gpt(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": content}]
        )
        print("GPTの応答:", response["choices"][0]["message"]["content"])
    except Exception as e:
        print("GPT送信エラー:", e)

# コールバックエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# テキストメッセージ処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_id = event.source.user_id
    text = event.message.text
    last_message_time[user_id] = datetime.now()
    
    # GPTに送信（返信はしない）
    threading.Thread(target=analyze_with_gpt, args=(text,)).start()
    
    # 5分後に返信スレッド起動
    threading.Thread(target=delayed_thanks, args=(user_id,)).start()

# 画像メッセージ処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    user_id = event.source.user_id
    last_message_time[user_id] = datetime.now()

    try:
        message_content = line_bot_api.get_message_content(event.message.id)
        image_data = b"".join(chunk for chunk in message_content.iter_content())
        analyze_with_gpt("画像が送信されました（バイナリデータ）")  # 実際の画像解析は別途APIが必要
    except Exception as e:
        print("画像処理エラー:", e)

    threading.Thread(target=delayed_thanks, args=(user_id,)).start()

# 起動コマンド（Render用）
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))