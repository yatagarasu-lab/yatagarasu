import os
import requests

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")  # 宛先ユーザーID（自分自身）

def send_line_message(text):
    if not LINE_CHANNEL_ACCESS_TOKEN or not USER_ID:
        print("⚠️ LINEの環境変数が未設定です")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    body = {
        "to": USER_ID,
        "messages": [
            {
                "type": "text",
                "text": text
            }
        ]
    }

    response = requests.post(url, headers=headers, json=body)
    if response.status_code != 200:
        print(f"❌ LINE通知エラー: {response.status_code} - {response.text}")
    else:
        print("✅ LINE通知送信完了")