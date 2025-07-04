import openai
import zipfile
import io
import os

# OpenAI APIキーを環境変数から読み込む
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_zip_content(zip_data: bytes) -> str:
    """
    ZIPファイルの内容を展開し、含まれるテキストをGPTに送って要約する
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
            result = ""
            for file_info in zf.infolist():
                if file_info.filename.endswith(".txt") or file_info.filename.endswith(".csv"):
                    with zf.open(file_info) as file:
                        content = file.read().decode("utf-8", errors="ignore")
                        print(f"🔍 {file_info.filename} をGPTで解析中...")

                        prompt = f"""以下のファイル「{file_info.filename}」の内容を要約・分析してください。
不要なデータは省略して重要な情報を抽出してください。日本語でお願いします。

内容:
{content[:2000]}"""  # 文字数制限のため先頭だけ送信

                        response = openai.ChatCompletion.create(
                            model="gpt-4-1106-preview",
                            messages=[
                                {"role": "system", "content": "あなたはDropbox内のデータを解析するプロです。"},
                                {"role": "user", "content": prompt}
                            ],
                            max_tokens=2000,
                            temperature=0.7
                        )

                        summary = response['choices'][0]['message']['content']
                        result += f"\n\n【{file_info.filename}】\n{summary}"

            return result.strip() or "⚠️ ZIPファイル内に解析対象ファイルがありませんでした。"

    except zipfile.BadZipFile:
        return "⚠️ ZIPファイルが壊れているか、読み込みできませんでした。"
    except Exception as e:
        return f"⚠️ GPT解析中にエラーが発生しました: {e}"