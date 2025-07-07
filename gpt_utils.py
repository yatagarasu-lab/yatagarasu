import openai
import os
import hashlib

openai.api_key = os.getenv("OPENAI_API_KEY")

def summarize_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下のテキストを要約してください。"},
                {"role": "user", "content": text}
            ],
            temperature=0.3,
            max_tokens=300
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print(f"[GPT要約エラー]: {e}")
        return "要約に失敗しました"

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def is_duplicate(new_content, existing_contents):
    new_hash = file_hash(new_content)
    return new_hash in {file_hash(c) for c in existing_contents}