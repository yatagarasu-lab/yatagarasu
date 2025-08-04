# services/gpt_summarizer.py

import openai
import os

def summarize_text(text):
    try:
        openai.api_key = os.environ.get("OPENAI_API_KEY")

        if not openai.api_key:
            return "🔑 OpenAI APIキーが設定されていません。"

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下のテキストを簡潔に要約してください。"},
                {"role": "user", "content": text}
            ],
            max_tokens=200,
            temperature=0.5
        )
        summary = response['choices'][0]['message']['content'].strip()
        return summary

    except Exception as e:
        return f"[要約エラー]: {str(e)}"
