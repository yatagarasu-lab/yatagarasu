# utils/image_ocr.py

import easyocr
from PIL import Image
import numpy as np
import io

reader = easyocr.Reader(["ja", "en"], gpu=False)  # 日本語・英語両対応

def extract_text_from_image_bytes(image_bytes):
    """
    画像バイトデータからテキストを抽出
    :param image_bytes: Dropboxから取得した画像のバイナリ
    :return: 認識されたテキスト（文字列）
    """
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(img)
        results = reader.readtext(img_np, detail=0)
        return "\n".join(results)
    except Exception as e:
        return f"[OCRエラー] {str(e)}"