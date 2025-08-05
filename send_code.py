import os
import requests

# E.T Code の受信先URL（RenderまたはローカルのURL）
ET_CODE_ENDPOINT = os.environ.get("ET_CODE_ENDPOINT", "https://et-code.onrender.com/receive-code")

# 送信するファイルのパス（例: scripts/sample.py）
FILE_TO_SEND = "scripts/sample.py"

def send_code():
    try:
        filename = os.path.basename(FILE_TO_SEND)

        with open(FILE_TO_SEND, "r", encoding="utf-8") as f:
            code = f.read()

        payload = {
            "filename": filename,
            "code": code
        }

        response = requests.post(ET_CODE_ENDPOINT, json=payload)

        print("送信完了:", response.status_code)
        print("レスポンス:", response.text)

    except Exception as e:
        print("送信失敗:", str(e))

if __name__ == "__main__":
    send_code()
