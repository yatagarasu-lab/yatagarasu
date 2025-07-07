import openai
import os

# OpenAI APIキーの読み込み
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# GPT-4でファイル内容を要約・解析する関数
def analyze_file_content(content, filename="ファイル"):
    try:
        # バイト型 → テキストへ変換（例：画像の場合はバイナリとして処理）
        if isinstance(content, bytes):
            try:
                content = content.decode("utf-8", errors="ignore")
            except Exception:
                return f"{filename} はバイナリ形式のファイルのため、テキスト解析できませんでした。"

        prompt = f"""
このファイル「{filename}」の内容を要約・解析してください。
以下がファイルの内容です（省略せず丁寧に処理してください）:

----------
{content}
----------
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはファイル解析と要約の専門家です。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )

        return response.choices[0].message["content"]

    except Exception as e:
        return f"{filename} の解析中にエラーが発生しました: {e}"