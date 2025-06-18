import os
import json
import requests
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 環境変数取得
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

line_bot_api = LineBotApi(LINE_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ✅ LINE Webhookエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
        print("LINEからPOST受信しました")
    except Exception as e:
        print(f"エラー: {e}")
        return "Error", 400

    return "OK", 200

# ✅ メッセージイベントの返信
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

# ✅ ミニロト予想（仮データ）
def get_miniloto_prediction():
    return [
        [5, 12, 18, 23, 29],
        [1, 11, 16, 20, 27],
        [3, 8, 13, 19, 25],
        [2, 9, 14, 21, 30],
        [4, 7, 17, 22, 28],
    ]

# ✅ 整形してLINEへ送信
def format_prediction(pred_list):
    message = "🎯【今週のミニロト予想】\n"
    for i, line in enumerate(pred_list, 1):
        message += f"{i}. {' '.join(f'{n:02d}' for n in line)}\n"
    return message

def send_line_message(message):
    url = 'https://api.line.me/v2/bot/message/broadcast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}',
    }
    payload = {
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, json=payload)

# ✅ 月曜8時に送信
def send_miniloto_prediction():
    pred = get_miniloto_prediction()
    msg = format_prediction(pred)
    send_line_message(msg)

# ✅ スケジューラー
scheduler = BackgroundScheduler()
scheduler.add_job(send_miniloto_prediction, 'cron', day_of_week='mon', hour=8, minute=0)
scheduler.start()

# ✅ サーバー起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)