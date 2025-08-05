# yatagarasu_sender.py（八咫烏側：E.T Code にコードを送る）

import requests

# E.T Code 側のエンドポイントURL（必ず https でRenderのURLを指定）
ETCODE_URL = "https://your-etcode-url.onrender.com/update-code"  # ←あなたの Render のURLに置き換えてください

def send_code(filename, code):
    payload = {
        "filename": filename,
        "code": code
    }

    try:
        response = requests.post(ETCODE_URL, json=payload)
        if response.status_code == 200:
            print(f"[成功] {filename} を E.T Code に送信しました。")
        else:
            print(f"[失敗] ステータス: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"[エラー] 送信中に問題が発生しました: {e}")

# テスト送信例
if __name__ == "__main__":
    code_to_send = """
print("これは八咫烏から送られたコードです！")
"""
    send_code("main.py", code_to_send)