# notifier.py

import os
import requests
from log_utils import log

# LINE Push通知を送る（ユーザーIDとトークンは環境変数）
LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")

def send_line_message(message):
    if not LINE_ACCESS_TOKEN or not USER_ID:
        log("⚠️ LINE設定が未定義のため通知スキップ")
        return

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }

    data = {
        "to": USER_ID,
        "messages": [
            {"type": "text", "text": message}
        ]
    }

    try:
        res = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)
        res.raise_for_status()
        log("✅ LINE通知成功")
    except Exception as e:
        log(f"❌ LINE通知エラー: {e}")

def notify(text, line=True, console=True):
    if console:
        log(text)
    if line:
        send_line_message(text)