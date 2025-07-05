import os
import requests
from dotenv import load_dotenv

# .env 読み込み
load_dotenv()

LINE_PUSH_ENABLED = os.getenv("LINE_PUSH_ENABLED", "false").lower() == "true"
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def send_line_message(message):
    if not LINE_PUSH_ENABLED:
        print("🔕 LINE通知は無効化されています")
        return

    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("❌ LINEのアクセストークンまたはユーザーIDが未設定です")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }

    data = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    url = "https://api.line.me/v2/bot/message/push"
    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        print(f"❌ LINE通知失敗: {response.status_code} {response.text}")
    else:
        print("✅ LINE通知送信完了")