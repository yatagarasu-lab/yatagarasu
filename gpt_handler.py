import zipfile
import io
import openai

# OpenAIのAPIキーは環境変数で設定しておく
openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_zip_content(zip_data: bytes) -> str:
    """
    ZIPファイル内のテキスト・画像をGPTで要約して返す。
    """
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data)) as zip_file:
            summaries = []

            for file_info in zip_file.infolist():
                filename = file_info.filename

                # テキストファイルの処理
                if filename.endswith(".txt"):
                    with zip_file.open(filename) as f:
                        content = f.read().decode("utf-8", errors="ignore")[:3000]  # 長すぎ防止
                        summary = summarize_text(content, filename)
                        summaries.append(summary)

                # 画像ファイルの処理（例：JPEG, PNG）
                elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
                    with zip_file.open(filename) as f:
                        image_bytes = f.read()
                        summary = summarize_image(image_bytes, filename)
                        summaries.append(summary)

            if not summaries:
                return "❗ ZIPファイル内に解析対象のファイルが見つかりませんでした。"

            return "\n\n---\n\n".join(summaries)

    except Exception as e:
        return f"❌ ZIP解析エラー: {e}"


def summarize_text(content: str, filename: str) -> str:
    """
    テキストをGPTで要約
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "これはDropboxに保存されたファイルの自動要約です。"},
                {"role": "user", "content": f"以下のファイル({filename})の内容を要約してください:\n\n{content}"}
            ],
            max_tokens=1000,
            temperature=0.3,
        )
        return f"[{filename}]の要約:\n{response.choices[0].message.content}"
    except Exception as e:
        return f"[{filename}]の要約失敗: {e}"


def summarize_image(image_bytes: bytes, filename: str) -> str:
    """
    画像をGPT-4 Visionで解析
    """
    try:
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "画像内容を解析して簡潔に説明してください。"},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{filename} という画像の内容を解説してください"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ],
            max_tokens=500
        )
        return f"[{filename}]の画像要約:\n{response.choices[0].message.content}"
    except Exception as e:
        return f"[{filename}]の画像要約失敗: {e}"