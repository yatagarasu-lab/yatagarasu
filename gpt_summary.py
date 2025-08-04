# gpt_summary.py

import openai
import os

# GPT要約の主処理
def summarize_file_content(content: str, file_name: str = "") -> str:
    try:
        prompt = f"""次の内容を200文字以内で要約してください。ファイル名: {file_name}\n\n内容:\n{content}"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは日本語に堪能な要約アシスタントです。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )

        summary = response['choices'][0]['message']['content'].strip()
        return summary

    except Exception as e:
        print(f"[GPT ERROR] 要約失敗: {e}")
        return "（要約エラー）"
