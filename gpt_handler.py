import zipfile
import io
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_zip_content(zip_bytes):
    """ZIPファイルをGPTに解析させて要約する処理"""

    # ZIP解凍
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
            summaries = []

            for name in zip_file.namelist():
                if name.endswith((".txt", ".csv", ".json", ".log")):
                    with zip_file.open(name) as file:
                        content = file.read().decode("utf-8", errors="ignore")

                        # GPTによる要約
                        summary = call_gpt_summary(content, name)
                        summaries.append(f"【{name}】\n{summary}\n")

            if summaries:
                return "\n".join(summaries)
            else:
                return "⚠️ ZIP内に解析対象ファイル（txt/csv/json/log）が見つかりませんでした。"

    except Exception as e:
        return f"❌ ZIP解析エラー: {e}"

def call_gpt_summary(text, filename=""):
    """GPTにテキストを送って要約させる処理"""

    prompt = f"""
あなたはDropboxに保存されたスロットの分析データを読んで要点を抽出するAIです。
ファイル名: {filename}
内容の要点、傾向、注目すべき点を箇条書きで3〜5行で日本語でまとめてください。

対象データ:
{text[:3000]}  # 長すぎると失敗するので先頭のみ使う
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # または gpt-3.5-turbo
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message["content"].strip()

    except Exception as e:
        return f"❌ GPT解析失敗: {e}"