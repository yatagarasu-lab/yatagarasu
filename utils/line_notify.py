import os
import requests

LINE_USER_ID = os.getenv("LINE_USER_ID")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

def send_line_message(message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }

    body = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }

    response = requests.post(
        "https://api.line.me/v2/bot/message/push",
        headers=headers,
        json=body
    )

    if response.status_code != 200:
        print(f"LINE通知失敗: {response.status_code} - {response.text}")
    else:
        print("LINE通知成功")