import openai
from utils import get_timestamp

openai.api_key = os.getenv("OPENAI_API_KEY")

# GPTによる自動要約・解析（テキスト or OCR結果に対応）
def analyze_content(file_name, content_text):
    prompt = f"""
以下の内容は、スロット設定情報・グラフ画像の解析ログ、またはメモです。
内容を要約し、必要に応じて「設定推測」「イベント名」「対象機種」「台番号」などを抽出してください。

【ファイル名】{file_name}
【内容】\n{content_text}

# 出力フォーマット（例）
- 要約: ○○○
- 機種: ○○○（ある場合）
- 台番号: ○○○（ある場合）
- 設定推測: ○○○（あれば）
- コメント: （自由欄）

日本語でわかりやすくまとめてください。
    """.strip()

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT解析エラー] {str(e)}"