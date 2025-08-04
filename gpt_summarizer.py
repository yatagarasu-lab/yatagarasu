# gpt_summarizer.py

import openai
import os

def summarize_file(filename, content):
    try:
        openai.api_key = os.getenv("OPENAI_API_KEY")
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはファイルの要約者です。"},
                {"role": "user", "content": f"次のファイルの内容を簡潔に要約してください:\n\n{content}"}
            ],
            max_tokens=300,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT要約エラー: {str(e)}"
