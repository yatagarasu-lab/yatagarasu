import os
import mimetypes
from dotenv import load_dotenv
from openai import OpenAI
from line_push import send_line_message

# .env 読み込み
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

client = OpenAI(api_key=OPENAI_API_KEY)

def analyze_file(file_path):
    mime_type, _ = mimetypes.guess_type(file_path)

    print(f"📝 解析対象: {file_path} (MIME: {mime_type})")

    if mime_type and mime_type.startswith("image/"):
        with open(file_path, "rb") as image_file:
            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "この画像の内容を要約してください。"},
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {
                            "url": f"data:{mime_type};base64,{image_file.read().encode('base64')}"
                        }}
                    ]}
                ]
            )
            result = response.choices[0].message.content

    elif mime_type == "application/pdf":
        import fitz  # PyMuPDF
        with fitz.open(file_path) as doc:
            text = ""
            for page in doc:
                text += page.get_text()
        result = gpt_summarize(text)

    else:
        # テキストファイル or その他
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        result = gpt_summarize(text)

    # ✅ LINE通知（先頭300字）
    send_line_message(f"✅ 解析完了: {os.path.basename(file_path)}\n\n{result[:300]}...")

    return result

def gpt_summarize(text):
    print("🔍 GPTによる要約中...")
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "以下のテキストを簡潔に要約してください。"},
            {"role": "user", "content": text[:4000]}
        ]
    )
    return response.choices[0].message.content