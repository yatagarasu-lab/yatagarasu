import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "短く簡潔に内容を要約してください"},
            {"role": "user", "content": text[:4000]}  # トークン制限考慮
        ]
    )
    return response['choices'][0]['message']['content'].strip()