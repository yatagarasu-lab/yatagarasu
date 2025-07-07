import os
import openai

# OpenAI APIキーを環境変数から取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# GPTでファイル内容を要約する関数
def analyze_content(file_content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # 必要に応じて "gpt-4o" に変更可能
            messages=[
                {
                    "role": "system",
                    "content": "あなたはファイルを要約するアシスタントです。内容を短く、分かりやすく要約してください。"
                },
                {
                    "role": "user",
                    "content": file_content.decode("utf-8", errors="ignore")[:4000]  # 長文対応（最大4,000文字）
                }
            ],
            temperature=0.2
        )
        summary = response.choices[0].message["content"]
        return summary
    except Exception as e:
        print(f"❌ GPT解析中にエラー発生: {e}")
        return "解析エラーが発生しました。"