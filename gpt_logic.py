import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_file(file_content, filename):
    try:
        content_str = file_content.decode('utf-8', errors='ignore')

        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは文書整理の専門AIです。スロット・パチンコに関する情報であれば解析・分類し、要点を要約してください。それ以外は『その他』として処理してください。"
                },
                {
                    "role": "user",
                    "content": f"ファイル名: {filename}\n\n内容:\n{content_str}"
                }
            ],
            temperature=0.3,
        )

        summary = response.choices[0].message['content']
        return summary

    except Exception as e:
        return f"解析失敗: {e}"
