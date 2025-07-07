import openai
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

# 画像の前処理
def preprocess_image(image_data):
    image = Image.open(image_data).convert("L")  # グレースケール
    image = image.filter(ImageFilter.MedianFilter())
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)  # コントラスト強調
    return image

# OCRからテキスト抽出
def extract_text(image):
    return pytesseract.image_to_string(image, lang="jpn")

# GPTによる要約＋設定推測
def summarize_text(text):
    prompt = f"""
以下はスロットのデータ画像から抽出したテキストです。
出現しているワード、設定差のあるゾーン、右肩上がりの表現、AT履歴などから、内容を要約し、
高設定の可能性があるかをコメントしてください。

特に以下の点を重視してください：
- 「朝カス」「1000カス」などの設定示唆ワード
- CZ履歴（150/250/450/650Gなど）
- 「右肩上がり」「2000枚」「差枚プラス」などの良挙動
- グラフの雰囲気（例：垂直、V字、安定）

【OCR抽出テキスト】
{text}
"""

    response = openai.ChatCompletion.create(
        model="gpt-4",
        temperature=0.3,
        messages=[
            {"role": "system", "content": "スロット台の設定推測アナリストとして、テキストを要約してください。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message["content"]

# 画像データ1枚を処理して要約返却
def analyze_file(filename, image_data):
    try:
        image = preprocess_image(image_data)
        text = extract_text(image)
        summary = summarize_text(text)
        return f"📄 {filename}:\n{summary}"
    except Exception as e:
        return f"⚠️ {filename}: 解析エラー - {str(e)}"