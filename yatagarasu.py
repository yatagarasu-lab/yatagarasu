# yatagarasu_sender.py（八咫烏側：E.T Code にコード送信）

import requests

ETCODE_URL = "https://your-etcode-url.onrender.com/update-code"  # ←正しいURLに変更

def send_code(filename, code):
    payload = {
        "filename": filename,
        "code": code
    }

    response = requests.post(ETCODE_URL, json=payload)

    if response.status_code == 200:
        print(f"[成功] {filename} を E.T Code に送信しました")
    else:
        print(f"[失敗] ステータス: {response.status_code}")
        print(response.text)

# テスト送信例
if __name__ == "__main__":
    code_to_send = """
print("これは八咫烏から送られたコードです！")
"""
    send_code("main.py", code_to_send)