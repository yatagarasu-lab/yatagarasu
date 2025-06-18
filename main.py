import os
import requests
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# Flaskアプリ作成
app = Flask(__name__)

# 環境変数からトークンなどを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LINE API 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ✅ Webhookエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print("Webhook Error:", e)
        return "Error", 400

    print("LINEからPOST受信しました")
    return "OK", 200

# ✅ ユーザーからのメッセージイベント処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text

    # 固定返信（変更可能）
    reply = "ありがとうございます"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

# ✅ ミニロト予想ロジック（仮・固定）
def get_miniloto_prediction():
    return [
        [5, 12, 18, 23, 29],
        [1, 11, 16, 20, 27],
        [3, 8, 13, 19, 25],
        [2, 9, 14, 21, 30],
        [4, 7, 17, 22, 28],
    ]

# ✅ メッセージ整形
def format_prediction(pred_list):
    message = "🎯【今週のミニロト予想】\n"
    for i, line in enumerate(pred_list, start=1):
        nums = " ".join(f"{n:02d}" for n in line)
        message += f"{i}. {nums}\n"
    return message

# ✅ LINE一斉送信
def send_line_message(message):
    url = 'https://api.line.me/v2/bot/message/broadcast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_CHANNEL_ACCESS_TOKEN}',
    }
    payload = {
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, json=payload)
    print("送信結果:", response.status_code, response.text)

# ✅ 毎週月曜 朝8時に自動通知
def send_miniloto_prediction():
    pred = get_miniloto_prediction()
    msg = format_prediction(pred)
    send_line_message(msg)

# スケジューラー起動
scheduler = BackgroundScheduler()
scheduler.add_job(send_miniloto_prediction, 'cron', day_of_week='mon', hour=8, minute=0)
scheduler.start()

# ✅ アプリ起動（Render用）
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)