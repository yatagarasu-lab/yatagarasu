import os
import io
import mimetypes
import hashlib
import numpy as np
from PIL import Image
import easyocr
import filetype

# OCRリーダー初期化（日本語＋英語）
ocr_reader = easyocr.Reader(['ja', 'en'], gpu=False)

def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def get_extension(content: bytes) -> str:
    kind = filetype.guess(content)
    return kind.extension if kind else "bin"

def is_image(filename: str) -> bool:
    ext = os.path.splitext(filename)[-1].lower()
    return ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]

def ocr_image_bytes(image_bytes: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(image)
        result = ocr_reader.readtext(img_np, detail=0)
        return "\n".join(result)
    except Exception as e:
        return f"OCR失敗: {e}"

def get_file_size_kb(content: bytes) -> float:
    return round(len(content) / 1024, 2)

def safe_decode(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return content.decode("shift_jis")
        except:
            return "[デコード不可] バイナリファイル"