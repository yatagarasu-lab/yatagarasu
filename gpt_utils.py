import hashlib
import openai
import os

# OpenAI APIキー（環境変数から取得）
openai.api_key = os.getenv("OPENAI_API_KEY")

def file_hash(content):
    """ファイルのSHA256ハッシュを計算して返す"""
    return hashlib.sha256(content).hexdigest()

def process_with_gpt(text):
    """テキストを要約・分類して返す（応答は使わないが記録可）"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下のテキストを要約・分析し、必要に応じて分類してください。"},
                {"role": "user", "content": text}
            ],
            temperature=0.5,
            max_tokens=500
        )
        result = response['choices'][0]['message']['content']
        print(f"🧠 GPT応答: {result}")
        return result
    except Exception as e:
        print(f"❌ GPTエラー: {e}")
        return None