import openai
import os

# OpenAIのAPIキー
openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはDropboxのファイル内容を要約・解析し、要点を抽出してレポートを作成するアシスタントです。"},
                {"role": "user", "content": f"このファイルの内容を要約してください:\n\n{text}"}
            ],
            temperature=0.3,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"[GPTエラー] {str(e)}"