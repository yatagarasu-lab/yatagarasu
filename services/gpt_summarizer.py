import openai
import os

# 環境変数からAPIキーを取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

def summarize_text(text, model="gpt-4", max_tokens=800):
    """
    テキストを要約するための関数
    """
    if not text or not OPENAI_API_KEY:
        return "⚠️ テキストが空、または API キーが設定されていません"

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "以下のテキストを日本語で要約してください。"},
                {"role": "user", "content": text}
            ],
            max_tokens=max_tokens,
            temperature=0.5,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"❌ GPT要約エラー: {e}"

def analyze_text(text, model="gpt-4", max_tokens=1000):
    """
    テキストの内容を分析・解釈して要点を出力する
    """
    if not text or not OPENAI_API_KEY:
        return "⚠️ テキストが空、または API キーが設定されていません"

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "以下の文章から重要な要点を抽出し、日本語で簡潔にまとめてください。"},
                {"role": "user", "content": text}
            ],
            max_tokens=max_tokens,
            temperature=0.5,
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"❌ GPT分析エラー: {e}"