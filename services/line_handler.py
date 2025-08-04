import os
import requests

# 環境変数からLINE BOTの情報を取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# LINEにメッセージをPush送信する関数
def push_line_message(message: str) -> bool:
    if not LINE_CHANNEL_ACCESS_TOKEN or not LINE_USER_ID:
        print("[エラー] LINEのトークンまたはユーザーIDが未設定です。")
        return False

    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            print("[LINE通知成功]")
            return True
        else:
            print(f"[LINE通知失敗] ステータスコード: {response.status_code} / 内容: {response.text}")
            return False
    except Exception as e:
        print(f"[LINE通知例外] {str(e)}")
        return False