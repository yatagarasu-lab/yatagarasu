# utils/image_ocr.py

import easyocr
from PIL import Image
import numpy as np
import io

# EasyOCR 初期化（日本語＋英語）
reader = easyocr.Reader(['ja', 'en'], gpu=False)

def extract_text_from_image_bytes(image_bytes):
    """
    バイトデータから画像を読み取り、OCRでテキストを抽出する
    :param image_bytes: 画像ファイルのバイナリデータ
    :return: 抽出されたテキスト（文字列）
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)

        results = reader.readtext(image_np, detail=0)
        return "\n".join(results).strip()
    except Exception as e:
        return f"OCR解析中にエラー: {e}"