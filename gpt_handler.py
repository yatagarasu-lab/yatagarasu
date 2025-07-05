import zipfile
import io
import openai
import os

# OpenAI APIキーの取得
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_zip_content(zip_binary):
    """ZIPファイルを解析し、含まれるテキストや画像を要約"""
    try:
        summary = ""
        with zipfile.ZipFile(io.BytesIO(zip_binary)) as zf:
            for file_info in zf.infolist():
                filename = file_info.filename

                # テキストファイルを読み取り・要約
                if filename.endswith(".txt"):
                    with zf.open(file_info) as f:
                        content = f.read().decode("utf-8", errors="ignore")
                        summary += f"▼ {filename} の要約:\n"
                        summary += gpt_summarize(content)
                        summary += "\n\n"

                # 画像ファイルも含まれていたらファイル名だけ列挙（今は要約しない）
                elif filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                    summary += f"📷 画像ファイル: {filename}\n"

        return summary.strip() or "ZIPファイルにテキストや画像が含まれていませんでした。"

    except Exception as e:
        return f"❌ ZIP解析エラー: {e}"

def gpt_summarize(text):
    """与えられた長文をGPTで要約"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "以下のテキストを日本語で簡潔に要約してください。"
                },
                {
                    "role": "user",
                    "content": text[:3000]  # 入力制限
                }
            ],
            max_tokens=1000,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"（GPT要約失敗: {e}）"