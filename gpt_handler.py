import zipfile
import io
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_zip_content(zip_bytes):
    """
    ZIPファイルの内容を抽出して、各ファイルをGPTで解析し、結果を1つのテキストとして返す。
    """
    try:
        result = []
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
            for file_name in zip_file.namelist():
                if file_name.endswith((".txt", ".csv", ".json")):
                    with zip_file.open(file_name) as f:
                        content = f.read().decode('utf-8', errors='ignore')

                    response = client.chat.completions.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "以下のデータを簡潔に要約し、重要な点を抽出してください。"},
                            {"role": "user", "content": content[:3000]}
                        ],
                        max_tokens=1000,
                        temperature=0.4,
                    )
                    result.append(f"🔹【{file_name}】\n{response.choices[0].message.content.strip()}\n")

        return "\n\n".join(result) if result else "⚠️ ZIP内に解析可能なファイルが見つかりませんでした。"

    except Exception as e:
        return f"❌ ZIP解析中にエラーが発生しました: {str(e)}"