import zipfile
import io
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_zip_content(zip_data: bytes) -> str:
    """
    ZIPデータを展開し、中身のテキスト・画像ファイルをGPTで解析して要約する。
    """
    try:
        summary = []

        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
            for filename in zip_file.namelist():
                if filename.endswith(".txt"):
                    content = zip_file.read(filename).decode("utf-8", errors="ignore")
                    gpt_summary = gpt_summarize(content)
                    summary.append(f"📝 {filename}:\n{gpt_summary}\n")

                elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    image_data = zip_file.read(filename)
                    gpt_image = gpt_image_analysis(image_data)
                    summary.append(f"🖼️ {filename}:\n{gpt_image}\n")

        if not summary:
            return "⚠️ ZIP内に対応可能なファイル（.txt/.jpg/.png）が見つかりませんでした。"

        return "\n\n".join(summary)

    except Exception as e:
        print(f"❌ ZIP解析エラー: {e}")
        return f"⚠️ ZIP解析中にエラーが発生しました: {e}"

def gpt_summarize(text: str) -> str:
    """
    テキストデータをGPTで要約する
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "以下の内容を簡潔に要約してください。"},
                {"role": "user", "content": text[:4000]}  # 長すぎる場合を考慮
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ テキスト要約エラー: {e}")
        return "⚠️ テキスト要約に失敗しました"

def gpt_image_analysis(image_data: bytes) -> str:
    """
    画像データをGPT-4oのvisionで解析して内容を説明する
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "この画像の内容を説明してください。"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data.decode('latin1')}"
                            }
                        },
                    ],
                }
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"❌ 画像解析エラー: {e}")
        return "⚠️ 画像解析に失敗しました"