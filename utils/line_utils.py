import os
import requests

LINE_API_URL = "https://api.line.me/v2/bot/message/push"
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

def send_custom_line_notification(user_id, summary_text, dropbox_path):
    """
    LINE Push通知をカスタムで送信
    """
    try:
        headers = {
            "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        message = {
            "to": user_id,
            "messages": [
                {
                    "type": "text",
                    "text": f"📝新しい解析結果が届きました！\n\n📄 要約:\n{summary_text}\n\n📁 保存先:\n{dropbox_path}"
                }
            ]
        }

        response = requests.post(LINE_API_URL, headers=headers, json=message)
        response.raise_for_status()

    except Exception as e:
        print(f"[LINE通知エラー] {e}")
