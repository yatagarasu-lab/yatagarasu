import zipfile
import io
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_zip_content(zip_bytes: bytes) -> str:
    """
    ZIPファイルの中身を解凍・要約し、GPTに渡して解析結果を返す
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
            summaries = []
            for filename in zip_file.namelist():
                if filename.endswith((".txt", ".csv", ".json", ".md", ".log")):
                    with zip_file.open(filename) as file:
                        content = file.read().decode("utf-8", errors="ignore")
                        summary = summarize_with_gpt(filename, content)
                        summaries.append(f"📄 {filename}:\n{summary}\n")
                else:
                    summaries.append(f"📁 {filename}: （非対応ファイル）")

            return "\n".join(summaries) if summaries else "⚠️ ZIP内に対応ファイルが見つかりませんでした。"

    except zipfile.BadZipFile:
        return "❌ ZIPファイルの形式が正しくありません。"

def summarize_with_gpt(filename: str, content: str) -> str:
    """
    GPTでファイル内容を要約する
    """
    prompt = f"""
以下はファイル「{filename}」の内容です。一言で要点をまとめてください。必要があれば詳細にも触れて構いません。

--- 内容開始 ---
{content[:2000]}  # GPT-4は長文に対応していますが、制限付きで切り取っています
--- 内容終了 ---
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはファイル要約の専門家です。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"❌ 要約中にエラー発生: {e}"