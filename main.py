import os
import requests
from flask import Flask, request, abort
from apscheduler.schedulers.background import BackgroundScheduler

# Flaskアプリ起動
app = Flask(__name__)

# 環境変数からトークンを取得
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LINE返信API
def reply_message(reply_token, message_text):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{
            "type": "text",
            "text": message_text
        }]
    }
    requests.post(url, headers=headers, json=payload)

# ミニロト予想
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

# ブロードキャスト送信（定期送信用）
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

# Webhookエンドポイント（LINEのメッセージ受信）
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json()
    print("LINE Webhook受信:", body)

    events = body.get("events", [])
    for event in events:
        if event.get("type") == "message":
            reply_token = event["replyToken"]
            user_msg = event["message"].get("text", "")
            if "ミニロト" in user_msg:
                pred = get_miniloto_prediction()
                msg = format_prediction(pred)
                reply_message(reply_token, msg)
            else:
                reply_message(reply_token, "ありがとうございます")

    return "OK", 200

# 毎週月曜8:00にミニロト予想をブロードキャスト
scheduler = BackgroundScheduler()
scheduler.add_job(lambda: send_line_message(format_prediction(get_miniloto_prediction())),
                  'cron', day_of_week='mon', hour=8, minute=0)
scheduler.start()

# サーバー起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)