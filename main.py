import os
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask

app = Flask(__name__)

LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")

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
        nums = " ".join(f"{n:02d}" for n in sorted(line))
        message += f"{i}. {nums}\n"
    return message

def send_line_message(message):
    url = 'https://api.line.me/v2/bot/message/broadcast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}'
    }
    payload = {
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, json=payload)

def send_miniloto_prediction():
    prediction = get_miniloto_prediction()
    message = format_prediction(prediction)
    send_line_message(message)

scheduler = BackgroundScheduler()
scheduler.add_job(send_miniloto_prediction, 'cron', day_of_week='sun', hour=8, minute=0)
scheduler.start()

@app.route("/")
def home():
    return "LINE Notification Bot is running"

if __name__ == "__main__":
    app.run()