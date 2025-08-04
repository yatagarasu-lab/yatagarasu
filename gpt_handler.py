# gpt_handler.py

import os
import openai
from dropbox_client import download_file
from log_utils import log

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_file_from_dropbox(file_path):
    try:
        content = download_file(file_path)
        text = content.decode("utf-8")

        log(f"📄 GPT解析中: {file_path}（{len(text)}文字）")

        # ChatGPTに要約させる
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下のテキストの要点を簡潔に日本語で要約してください。"},
                {"role": "user", "content": text}
            ],
            max_tokens=800
        )

        summary = response['choices'][0]['message']['content'].strip()
        log(f"✅ GPT要約成功: {file_path}")
        return summary

    except Exception as e:
        log(f"❌ GPT要約エラー: {str(e)}")
        return None