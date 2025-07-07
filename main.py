from flask import Flask, request
import os
import requests

app = Flask(__name__)

# Pushメッセージを送信する関数
def push_message(user_id, message):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {os.environ["LINE_CHANNEL_ACCESS_TOKEN"]}'
    }
    data = {
        'to': user_id,
        'messages': [{'type': 'text', 'text': message}]
    }

    response = requests.post(url, headers=headers, json=data)

    # デバッグログ出力（成功 or エラー確認用）
    print("LINE Push status:", response.status_code)
    print("LINE Push response:", response.text)

# Webhookエンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json()
    print("📩 Webhook Received:", body)

    # ユーザーIDがある場合は確認メッセージを返信
    try:
        user_id = body["events"][0]["source"]["userId"]
        push_message(user_id, "ありがとうございます")  # 固定返信
    except Exception as e:
        print("⚠️ ユーザーID取得失敗 or Pushエラー:", e)

    return "OK", 200

# 動作確認用のルート
@app.route("/")
def index():
    return "LINE BOT 起動中"

if __name__ == "__main__":
    app.run()