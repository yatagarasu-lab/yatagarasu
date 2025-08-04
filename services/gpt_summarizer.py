import os
import openai

# 環境変数からAPIキーを取得
openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_text(text, max_tokens=300):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下の内容を簡潔に要約してください。"},
                {"role": "user", "content": text}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        summary = response['choices'][0]['message']['content'].strip()
        return summary
    except Exception as e:
        print(f"要約エラー: {e}")
        return "要約に失敗しました。"

def analyze_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下の内容を分析してください。必要に応じて改善提案も加えてください。"},
                {"role": "user", "content": text}
            ],
            max_tokens=500,
            temperature=0.5
        )
        analysis = response['choices'][0]['message']['content'].strip()
        return analysis
    except Exception as e:
        print(f"解析エラー: {e}")
        return "解析に失敗しました。"