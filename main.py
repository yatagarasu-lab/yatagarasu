import os
import json
import requests
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# 環境変数からトークン取得
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ======== ミニロト予想と通知関数 ========

def get_miniloto_prediction():
    return [
        [5, 12, 18, 23, 29],
        [1, 11, 16, 20, 27],
        [3, 8, 13, 19, 25],
        [2, 9, 14, 21, 30],
        [4, 7, 17, 22, 28],
    ]

def format_prediction(pred_list):
    message = "🎯【今週のミニロト予想】\n"
    for i, line in enumerate(pred_list, start=1):
        nums = " ".join(f"{n:02d}" for n in line)
        message += f"{i}. {nums}\n"
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

def send_miniloto_prediction():
    pred = get_miniloto_prediction()
    msg = format_prediction(pred)
    send_line_message(msg)

# ======== Webhook応答機能 ========

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json()
    print("LINEからPOST受信:", body)

    try:
        events = body["events"]
        for event in events:
            if event["type"] == "message" and event["message"]["type"] == "text":
                reply_token = event["replyToken"]
                user_message = event["message"]["text"]

                reply_message = {
                    "replyToken": reply_token,
                    "messages": [{
                        "type": "text",
                        "text": "ありがとうございます"
                    }]
                }

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
                }

                requests.post("https://api.line.me/v2/bot/message/reply",
                              headers=headers, json=reply_message)

    except Exception as e:
        print("エラー:", e)

    return "OK", 200

# ======== スケジューラー（毎週月曜8:00に通知） ========

scheduler = BackgroundScheduler()
scheduler.add_job(send_miniloto_prediction, 'cron', day_of_week='mon', hour=8, minute=0)
scheduler.start()

# ======== Flaskサーバー起動 ========

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)