import os
import io
import zipfile
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_zip_content(zip_binary):
    """ZIPファイルの中身を展開し、各ファイルをGPTで解析して結果をまとめる"""
    results = []

    try:
        with zipfile.ZipFile(io.BytesIO(zip_binary)) as zipf:
            for name in zipf.namelist():
                if name.endswith("/"):
                    continue  # ディレクトリはスキップ
                content = zipf.read(name).decode("utf-8", errors="ignore")
                summary = gpt_summarize(name, content)
                results.append(f"📝 {name} の解析結果:\n{summary}\n")

        return "\n\n".join(results) if results else "⚠️ ZIPファイル内に解析可能なファイルがありませんでした。"

    except Exception as e:
        return f"❌ ZIP解析エラー: {e}"

def gpt_summarize(filename, content):
    """GPTにファイル内容の要約・解析を依頼"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたはデータ分析に長けたアシスタントです。"},
                {"role": "user", "content": f"以下のファイル「{filename}」の内容を読み取り、要点・傾向・異常点などを簡潔にまとめてください。\n\n{content}"}
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"⚠️ GPT解析エラー: {e}"