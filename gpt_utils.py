import openai
import os

# OpenAI APIキー（環境変数から取得）
openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_text(text):
    """
    テキストをGPTで要約する関数
    """
    try:
        print("🧠 GPTで要約中...")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下のテキストを簡潔に要約してください。"},
                {"role": "user", "content": text}
            ],
            temperature=0.3
        )
        summary = response.choices[0].message["content"].strip()
        print("✅ 要約完了")
        return summary
    except Exception as e:
        print(f"❌ GPT要約エラー: {e}")
        return "要約に失敗しました。"