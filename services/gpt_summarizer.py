import openai
import os

# 環境変数からAPIキー取得
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GPTで要約を実行する関数
def summarize_text(text: str, max_tokens: int = 300) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY が設定されていません。")

    openai.api_key = OPENAI_API_KEY

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下の内容を簡潔に要約してください。"},
                {"role": "user", "content": text},
            ],
            max_tokens=max_tokens,
            temperature=0.5,
        )
        return response.choices[0].message["content"].strip()

    except Exception as e:
        print(f"[GPT要約エラー] {str(e)}")
        return "要約に失敗しました。"

# GPTでファイル名用のタイトル生成（任意機能）
def generate_title(text: str) -> str:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY が設定されていません。")

    openai.api_key = OPENAI_API_KEY

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下のテキストの内容から、ファイル名に使える短いタイトルを生成してください。"},
                {"role": "user", "content": text},
            ],
            max_tokens=40,
            temperature=0.5,
        )
        return response.choices[0].message["content"].strip()

    except Exception as e:
        print(f"[GPTタイトル生成エラー] {str(e)}")
        return "untitled"