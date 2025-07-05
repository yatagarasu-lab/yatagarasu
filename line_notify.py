import os
import json
import requests

# あなたのユーザーID（固定）
USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"

# LINEチャンネルアクセストークン（環境変数で設定）
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

def push_message(text):
    if not CHANNEL_ACCESS_TOKEN:
        print("❌ LINEのトークンが未設定です")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}"
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": text}]
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code != 200:
        print(f"❌ LINE通知失敗: {response.text}")
    else:
        print("✅ LINE通知を送信しました")