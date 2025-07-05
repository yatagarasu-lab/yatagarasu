import zipfile
import openai
import os
from io import BytesIO

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_zip_content(zip_data: bytes) -> str:
    try:
        result_summary = []

        with zipfile.ZipFile(BytesIO(zip_data)) as zip_file:
            for file_info in zip_file.infolist():
                if file_info.filename.endswith(".txt"):
                    with zip_file.open(file_info.filename) as f:
                        content = f.read().decode("utf-8", errors="ignore")
                        summary = summarize_text(content, file_info.filename)
                        result_summary.append(summary)

        return "\n\n".join(result_summary)

    except Exception as e:
        return f"ZIP解析中にエラーが発生しました: {e}"

def summarize_text(text: str, filename: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",  # 必要に応じて変更可能
            messages=[
                {"role": "system", "content": "あなたは要約のプロです。内容をできる限り簡潔にわかりやすく要約してください。"},
                {"role": "user", "content": f"次のテキストファイル（{filename}）の要約をお願いします:\n\n{text[:4000]}"}
            ],
            temperature=0.3,
        )
        summary = response.choices[0].message.content.strip()
        return f"🗂 {filename} の要約:\n{summary}"

    except Exception as e:
        return f"要約エラー（{filename}）: {e}"