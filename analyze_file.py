import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# OpenAIクライアントの初期化（proxiesを除外）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_file(file_path):
    try:
        # ファイル内容を読み込む（テキスト or OCR前提）
        with open(file_path, "rb") as f:
            file_bytes = f.read()

        # OpenAI API に送信して解析（例: GPT-4oを使う）
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[
                {"role": "system", "content": "あなたは画像や文章を解析するAIアシスタントです。"},
                {"role": "user", "content": "次のファイルを読み取り、要約してください。"},
                {"role": "user", "content": file_bytes.decode("utf-8", errors="ignore")},
            ],
            temperature=0.3
        )

        # 応答を取得
        return response.choices[0].message.content

    except Exception as e:
        return f"解析中にエラーが発生しました: {e}"