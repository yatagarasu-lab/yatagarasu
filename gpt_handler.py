import openai
import zipfile
import io
import os

# OpenAI APIキーを環境変数から取得（Renderに登録済みの前提）
openai.api_key = os.getenv("OPENAI_API_KEY")


def analyze_text_file(file_content: bytes) -> str:
    """テキストファイルの中身をGPTで要約・分析"""
    try:
        text = file_content.decode("utf-8", errors="ignore")

        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "あなたはファイル解析アシスタントです。"},
                {"role": "user", "content": f"以下の内容を要約・分析してください:\n\n{text}"}
            ],
            temperature=0.5
        )
        return response.choices[0].message["content"]

    except Exception as e:
        return f"⚠️ GPT解析エラー（テキスト）: {e}"


def analyze_image_file(file_content: bytes) -> str:
    """画像ファイルをGPTに解析してもらう（Vision API）"""
    try:
        base64_image = file_content.encode("base64")
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {"role": "system", "content": "あなたは画像解析アシスタントです。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                        {"type": "text", "text": "この画像の内容を説明してください。"}
                    ]
                }
            ],
            temperature=0.2,
        )
        return response.choices[0].message["content"]

    except Exception as e:
        return f"⚠️ GPT解析エラー（画像）: {e}"


def analyze_zip_content(zip_data: bytes) -> str:
    """ZIPファイル内のファイルをすべてGPTで解析"""
    result_summary = []
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as archive:
            for name in archive.namelist():
                with archive.open(name) as f:
                    content = f.read()

                if name.endswith(".txt"):
                    result = analyze_text_file(content)
                elif name.endswith((".jpg", ".jpeg", ".png")):
                    result = analyze_image_file(content)
                else:
                    result = f"⚠️ 未対応ファイル形式: {name}"

                result_summary.append(f"🔹 {name}:\n{result}\n")

        return "\n".join(result_summary)
    except Exception as e:
        return f"⚠️ ZIP解析エラー: {e}"
