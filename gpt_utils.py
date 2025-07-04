# gpt_utils.py
import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_file_content(content):
    """
    GPTでファイルの内容を解析し、要約または重要情報を抽出。
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下のテキストファイルの内容を要約または重要な情報を抽出してください。"},
                {"role": "user", "content": content}
            ]
        )
        summary = response['choices'][0]['message']['content']
        return summary.strip()
    except Exception as e:
        return f"解析中にエラーが発生しました: {str(e)}"