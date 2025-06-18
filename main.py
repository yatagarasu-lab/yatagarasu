import os
import requests
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# 環境変数からトークン取得
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ミニロト予想（仮固定。AI連携も可）
def get_miniloto_prediction():
    return [
        [1, 5, 11, 18, 26],
        [3, 9, 14, 20, 29],
        [2, 8, 13, 21, 30],
        [4, 7, 17, 22, 28],
        [6, 10, 15, 23, 27],
    ]

# スロット予想（サンプル固定）
def get_slot_recommendation():
    return [
        "📍ガイア川崎 → 北斗の拳（並び）1101〜1103",
        "📍楽園川崎 → 番長4 単品で投入傾向あり",
        "📍123横浜西口 → マギレコ or グールに注意"
    ]

# LINE用に整形
def format_message(miniloto, slot):
    message = "🎯【今週のミニロト予想】\n"
    for i, line in enumerate(miniloto, 1):
        nums = " ".join(f"{n:02d}" for n in line)
        message += f"{i}. {nums}\n"

    message += "\n🎰【今日のスロットおすすめ】\n"
    for line in slot:
        message += f"{line}\n"
    return message

# LINEに通知
def send_line_message(message):
    url = 'https://api.line.me/v2/bot/message/broadcast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}',
    }
    payload = {
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, json=payload)
    print("LINE送信ステータス:", response.status_code)
    print("レスポンス:", response.text)

# 通知関数（定期 or 手動）
def send_combined_notification():
    miniloto = get_miniloto_prediction()
    slot = get_slot_recommendation()
    msg = format_message(miniloto, slot)
    send_line_message(msg)

# Webhook（未使用でもOK）
@app.route("/callback", methods=["POST"])
def callback():
    print("LINE Webhook受信")
    return "OK", 200

# スケジューラー起動（月曜朝8時）
scheduler = BackgroundScheduler()
scheduler.add_job(send_combined_notification, 'cron', day_of_week='mon', hour=8, minute=0)
scheduler.start()

# Flask起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)