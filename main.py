from flask import Flask, request, abort
import requests
import os

app = Flask(__name__)

# 環境変数からLINEアクセストークンを取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

def push_message(user_id, message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    body = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    response = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=body
    )
    return response.status_code, response.text

@app.route("/", methods=["GET"])
def health_check():
    return "OK", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        body = request.get_json()
        print("Webhook received:", body)

        for event in body["events"]:
            if event["type"] == "message":
                user_id = event["source"]["userId"]
                message_text = event["message"]["text"]

                # 🔽 ここでDropboxへのファイル保存やGPT解析を追加予定
                # → 受信メッセージを処理し、結果をDropboxやGPTと連携

                # 固定返信（例：ありがとうございます）
                push_message(user_id, "ありがとうございます")

        return "OK", 200
    except Exception as e:
        print("Error in webhook:", e)
        abort(400)

if __name__ == "__main__":
    app.run()