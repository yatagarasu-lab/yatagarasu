import os
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import openai
from line_push import send_line_message

openai.api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("OPENAI_MODEL", "gpt-4o")

def analyze_file(file_path):
    content = ""

    # 拡張子で処理を分岐
    _, ext = os.path.splitext(file_path.lower())

    try:
        if ext == ".pdf":
            content = extract_text_from_pdf(file_path)
        elif ext in [".jpg", ".jpeg", ".png", ".webp"]:
            content = extract_text_from_image(file_path)
        else:
            content = extract_text_from_txt(file_path)

        # GPTに要約を依頼
        result = summarize_with_gpt(content)

        # ✅ LINEに通知を送信（長すぎる場合はカット）
        send_line_message(f"✅ 解析完了: {os.path.basename(file_path)}\n\n{result[:300]}...")

        return result

    except Exception as e:
        error_message = f"❌ ファイル解析中にエラーが発生しました: {e}"
        send_line_message(error_message)
        return error_message


def extract_text_from_pdf(file_path):
    text = ""
    with fitz.open(file_path) as pdf:
        for page in pdf:
            text += page.get_text()
    return text


def extract_text_from_image(file_path):
    image = Image.open(file_path)
    text = pytesseract.image_to_string(image, lang="jpn")
    return text


def extract_text_from_txt(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def summarize_with_gpt(content):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "以下の内容をわかりやすく要約してください。"},
            {"role": "user", "content": content}
        ],
        max_tokens=1000,
        temperature=0.5,
    )
    return response.choices[0].message["content"].strip()