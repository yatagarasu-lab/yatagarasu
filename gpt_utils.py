import openai
import os
from line_utils import push_message

# OpenAIの設定
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_and_notify(filename, content):
    try:
        print(f"🧠 GPT解析開始: {filename}")

        # バイナリ → テキスト（画像 or テキストファイル対応）
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            base64_data = content.encode("base64")  # ※古いPythonならbase64.b64encode
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_data}",
                                },
                            },
                            {"type": "text", "text": "この画像の要点を要約してください。"}
                        ],
                    }
                ],
            )
            summary = response.choices[0].message.content.strip()
        else:
            text = content.decode("utf-8", errors="ignore")
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "あなたは優秀な要約AIです。"},
                    {"role": "user", "content": f"以下を要約してください:\n\n{text}"}
                ],
            )
            summary = response.choices[0].message.content.strip()

        print("✅ GPT要約完了")
        push_message(f"📂 {filename} の要約:\n{summary}")

    except Exception as e:
        print(f"❌ GPT解析中にエラー: {e}")
        push_message(f"⚠️ GPT解析エラー: {filename}")