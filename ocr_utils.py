import pytesseract
from PIL import Image
import io

def extract_text_from_image(file_path):
    """
    指定された画像ファイルからOCRでテキストを抽出
    """
    try:
        with open(file_path, 'rb') as f:
            image = Image.open(io.BytesIO(f.read()))
            text = pytesseract.image_to_string(image, lang='jpn')
        return text.strip()
    except Exception as e:
        return f"[OCR失敗] {e}"
