# notifier.py 📡 LINEなどに通知送信するための共通ユーティリティ
import os
import requests

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# LINEへPush通知
def send_line_message(message):
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("❌ LINE通知に必要な環境変数が未設定です。")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    body = {
        "to": LINE_USER_ID,
        "messages": [
            {"type": "text", "text": message}
        ]
    }
    response = requests.post(url, headers=headers, json=body)
    
    if response.status_code != 200:
        print(f"❌ LINE通知送信失敗: {response.status_code} - {response.text}")
    else:
        print("✅ LINE通知送信完了")