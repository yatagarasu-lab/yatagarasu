import os
import requests

def send_code_to_et(filename: str, code: str):
    endpoint = os.environ.get("ET_CODE_ENDPOINT")
    if not endpoint:
        raise EnvironmentError("ET_CODE_ENDPOINT is not set in environment variables.")

    payload = {
        "filename": filename,
        "code": code
    }

    try:
        response = requests.post(endpoint, json=payload)
        response.raise_for_status()
        print(f"[✅] 送信成功: {response.json()}")
    except Exception as e:
        print(f"[❌] 送信エラー: {e}")

# 例：実行
if __name__ == "__main__":
    # ここは任意のテストコードに差し替えてください
    sample_code = "print('Hello from 八咫烏!')"
    send_code_to_et("hello_et.py", sample_code)