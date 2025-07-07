import hashlib
import openai
import os
from line_push import send_line_message

# OpenAI APIキー
openai.api_key = os.getenv("OPENAI_API_KEY")

# ファイルのハッシュ値を計算（重複チェック用）
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# GPT解析してLINEへ通知
def analyze_file_and_notify(filename, content):
    try:
        # ファイル内容を文字列に変換（画像なども将来対応可）
        text = content.decode("utf-8", errors="ignore")

        # GPT解析リクエスト
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは分析の専門家です。ファイル内容を要約し、重要なポイントを抽出してください。"},
                {"role": "user", "content": f"以下のファイルの内容を分析してください:\n{text}"}
            ],
            temperature=0.3,
            max_tokens=800
        )

        result = response["choices"][0]["message"]["content"]
        message = f"📄 ファイル `{filename}` の解析結果:\n\n{result}"
        send_line_message(message)

    except Exception as e:
        send_line_message(f"⚠️ GPT解析エラー: {e}")
