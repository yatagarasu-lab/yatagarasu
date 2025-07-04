# line_utils.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

def push_message_to_line(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    body = {
        "to": LINE_USER_ID,
        "messages": [
            {"type": "text", "text": message}
        ]
    }
    try:
        requests.post(url, headers=headers, json=body)
    except Exception as e:
        print(f"LINE送信失敗: {str(e)}")
