import os
import hashlib
import dropbox
from dropbox.files import FileMetadata
from PIL import Image
import pytz
from datetime import datetime
import easyocr
import io
import openai
from utils.logger import log_event

# Dropbox 初期化
DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

# GPT設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# OCRリーダー（EasyOCR）
reader = easyocr.Reader(['ja', 'en'], gpu=False)

# ファイルハッシュで重複検出
def file_hash(data):
    return hashlib.md5(data).hexdigest()

def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

# ファイルタイプ判定（拡張子で判別）
def get_file_type(filename):
    ext = filename.lower().split('.')[-1]
    if ext in ['jpg', 'jpeg', 'png', 'bmp']:
        return 'image'
    elif ext in ['txt', 'csv', 'log']:
        return 'text'
    elif ext in ['pdf']:
        return 'pdf'
    return 'unknown'

# OCR画像処理
def perform_ocr(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    result = reader.readtext(image)
    text = "\n".join([line[1] for line in result])
    return text

# GPTで要約
def summarize_with_gpt(text):
    if not text.strip():
        return "テキストが抽出できませんでした。"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下のテキストを要約してください"},
                {"role": "user", "content": text}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"GPTエラー: {str(e)}"

# メイン処理
def process_file(path):
    try:
        content = download_file(path)
        hash_value = file_hash(content)
        file_type = get_file_type(path)

        log_event(f"[処理開始] {path} / 種別: {file_type}")

        if file_type == "image":
            text = perform_ocr(content)
            summary = summarize_with_gpt(text)
        elif file_type == "text":
            text = content.decode("utf-8")
            summary = summarize_with_gpt(text)
        else:
            summary = "このファイル形式は未対応です。"

        log_event(f"[処理完了] {path}\n要約: {summary}")
        return summary

    except Exception as e:
        log_event(f"[エラー] {path}: {str(e)}")
        return "解析中にエラーが発生しました。"