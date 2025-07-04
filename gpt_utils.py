import openai
import os

# OpenAI APIキーを環境変数から取得
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# GPTでテキストを処理する関数
def process_with_gpt(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはDropboxに保存されたスロット関連データを解析・要約するAIアシスタントです。"},
                {"role": "user", "content": user_input}
            ],
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"GPT処理中にエラーが発生しました: {e}"