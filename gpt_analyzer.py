import os
import openai
from dropbox_helper import download_file

openai.api_key = os.getenv("OPENAI_API_KEY")

# ファイル内容をテキストとしてGPTで要約・解析
def analyze_file_from_dropbox(path):
    try:
        content = download_file(path)

        # 画像ファイルならOCRや画像解析へ（簡易判定）
        if path.lower().endswith((".png", ".jpg", ".jpeg")):
            return "[画像解析未実装]"

        # テキストベースなら要約
        text = content.decode("utf-8", errors="ignore")
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "以下のテキストデータを要約し、重要な情報や特徴があれば箇条書きで提示してください。"},
                {"role": "user", "content": text[:3000]}  # 長すぎ防止
            ],
            temperature=0.3
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"解析エラー: {str(e)}"