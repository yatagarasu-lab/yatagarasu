import os
import json
import requests
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# 環境変数
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ✅ /callback 定義（メッセージ受信→返信あり）
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json()
    print("LINEからPOST受信:", json.dumps(body, ensure_ascii=False))

    try:
        events = body.get("events", [])
        for event in events:
            if event.get("type") == "message" and event["message"]["type"] == "text":
                reply_token = event["replyToken"]
                reply_text = "ありがとうございます"

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
                }

                payload = {
                    "replyToken": reply_token,
                    "messages": [{
                        "type": "text",
                        "text": reply_text
                    }]
                }

                res = requests.post("https://api.line.me/v2/bot/message/reply",
                                    headers=headers, json=payload)
                print("返信結果:", res.status_code, res.text)

    except Exception as e:
        print("エラー:", e)

    return "OK", 200


# 🎯 ミニロト通知（毎週月曜8:00）
def get_miniloto_prediction():
    return [
        [5, 

以下が**LINE返信 + ミニロト自動通知**の両方に対応した、完成版 `main.py` です。

---

## ✅ 完全版 `main.py`

```python
import os
import json
import requests
from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# 環境変数
LINE_ACCESS_TOKEN = os.getenv("LINE_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 🎯 ミニロト予想関数（仮）
def get_miniloto_prediction():
    return [
        [5, 12, 18, 23, 29],
        [1, 11, 16, 20, 27],
        [3, 8, 13, 19, 25],
        [2, 9, 14, 21, 30],
        [4, 7, 17, 22, 28],
    ]

# 整形関数
def format_prediction(pred_list):
    message = "🎯【今週のミニロト予想】\n"
    for i, line in enumerate(pred_list, start=1):
        nums = " ".join(f"{n:02d}" for n in line)
        message += f"{i}. {nums}\n"
    return message

# LINE一斉送信
def send_line_message(message):
    url = 'https://api.line.me/v2/bot/message/broadcast'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {LINE_ACCESS_TOKEN}',
    }
    payload = {
        "messages": [{"type": "text", "text": message}]
    }
    res = requests.post(url, headers=headers, json=payload)
    print("LINE送信結果:", res.status_code, res.text)

# 定期実行ジョブ（月曜8:00）
def send_miniloto_prediction():
    pred = get_miniloto_prediction()
    msg = format_prediction(pred)
    send_line_message(msg)

# ✅ Webhookエンドポイント（応答用）
@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_json()
    print("LINEから受信:", json.dumps(body, ensure_ascii=False))

    try:
        events = body.get("events", [])
        for event in events:
            if event.get("type") == "message" and event["message"]["type"] == "text":
                reply_token = event["replyToken"]
                reply_text = "ありがとうございます"

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
                }

                payload = {
                    "replyToken": reply_token,
                    "messages": [{
                        "type": "text",
                        "text": reply_text
                    }]
                }

                res = requests.post("https://api.line.me/v2/bot/message/reply",
                                    headers=headers, json=payload)
                print("返信結果:", res.status_code, res.text)

    except Exception as e:
        print("エラー:", e)

    return "OK", 200

# スケジューラー開始
scheduler = BackgroundScheduler()
scheduler.add_job(send_miniloto_prediction, 'cron', day_of_week='mon', hour=8, minute=0)
scheduler.start()

# サーバー起動
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)