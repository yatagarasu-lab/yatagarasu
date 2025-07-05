import zipfile
import io
import openai
import os
from PIL import Image
import base64

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_zip_content(zip_bytes):
    try:
        result_summary = ""
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
            for file_info in z.infolist():
                with z.open(file_info.filename) as f:
                    content = f.read()

                    if file_info.filename.lower().endswith((".txt", ".csv")):
                        text = content.decode("utf-8", errors="ignore")
                        result = ask_gpt(text)
                        result_summary += f"🔹 {file_info.filename}\n{result}\n\n"

                    elif file_info.filename.lower().endswith((".jpg", ".jpeg", ".png")):
                        result = ask_gpt_image(content)
                        result_summary += f"🖼 {file_info.filename}\n{result}\n\n"

        return result_summary if result_summary else "⚠️ ZIP内に解析可能なファイルが見つかりませんでした。"

    except Exception as e:
        return f"❌ ZIP解析エラー: {e}"

def ask_gpt(text):
    response = openai.ChatCompletion.create(
        model="gpt-4-1106-preview",
        messages=[
            {"role": "system", "content": "以下のデータを要約・分析してください。"},
            {"role": "user", "content": text}
        ],
        temperature=0.5,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

def ask_gpt_image(image_bytes):
    try:
        b64_image = base64.b64encode(image_bytes).decode("utf-8")
        response = openai.ChatCompletion.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "この画像の内容を要約・分析してください"},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}
                    ],
                }
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ 画像解析エラー: {e}"