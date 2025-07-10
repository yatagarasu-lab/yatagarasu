# utils/image_ocr.py

import easyocr
import numpy as np
from PIL import Image
import io

# OCRリーダーの初期化（日本語と英語を対象に）
reader = easyocr.Reader(['ja', 'en'], gpu=False)

def extract_text_from_image(image_bytes: bytes) -> str:
    """
    画像のバイナリデータから文字を抽出する
    :param image_bytes: 画像データ（バイナリ）
    :return: 抽出された文字列
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image_np = np.array(image)
        results = reader.readtext(image_np, detail=0)
        text = "\n".join(results)
        return text.strip()
    except Exception as e:
        return f"[OCR解析エラー]: {str(e)}"
