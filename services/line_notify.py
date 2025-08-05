import os
import requests
import json

# 環境変数からLINEのチャネルアクセストークンとユーザーIDを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def send_line_message(message: str):
    """
    LINE Pushメッセージを送信する関数
    """
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("❌ LINEの環境変数が設定されていません")
        return

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }

    body = {
        "to": LINE_USER_ID,
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))

    if response.status_code == 200:
        print("✅ LINE通知を送信しました")
    else:
        print(f"❌ LINE通知に失敗しました: {response.status_code} - {response.text}")