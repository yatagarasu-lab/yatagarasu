import openai
import os

# OpenAI APIキー
openai.api_key = os.getenv("OPENAI_API_KEY")

def process_with_gpt(text):
    """テキストをGPTで要約または整形する（今はLINE返信は固定）"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはスロットデータを解析する専門AIです。"},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=800
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print(f"❌ GPT処理失敗: {e}")
        return "GPT処理に失敗しました。"