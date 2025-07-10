import os
import dropbox
from PIL import Image
from io import BytesIO
import pytz
import datetime
import openai
import easyocr
import numpy as np

from utils.line_notify import send_line_message
from utils.file_utils import list_files, download_file, file_hash, is_duplicate

# Dropbox アクセス
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

# OpenAI キー
openai.api_key = os.getenv("OPENAI_API_KEY")

# LINE 通知先
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 初期化
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET,
)


def summarize_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "以下のテキストを要約してください"},
                {"role": "user", "content": text},
            ],
            max_tokens=1024,
            temperature=0.2
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[要約エラー]: {str(e)}"


def extract_text_from_image(image_bytes):
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        reader = easyocr.Reader(['ja', 'en'], gpu=False)
        result = reader.readtext(np.array(image), detail=0)
        return "\n".join(result)
    except Exception as e:
        return f"[画像解析エラー]: {str(e)}"


def analyze_file(path):
    try:
        content = download_file(path)
        ext = os.path.splitext(path)[1].lower()

        if ext in [".png", ".jpg", ".jpeg", ".bmp", ".webp"]:
            extracted_text = extract_text_from_image(content)
            summary = summarize_text(extracted_text)
            return f"📸 {os.path.basename(path)}\n{summary}"

        elif ext in [".txt", ".csv", ".log"]:
            text = content.decode("utf-8", errors="ignore")
            summary = summarize_text(text)
            return f"📄 {os.path.basename(path)}\n{summary}"

        else:
            return f"❓未対応ファイル: {os.path.basename(path)}"

    except Exception as e:
        return f"[解析エラー]: {os.path.basename(path)} - {str(e)}"


def analyze_dropbox_and_notify():
    try:
        files = list_files("/Apps/slot-data-analyzer")
        if not files:
            send_line_message(LINE_USER_ID, "Dropboxにファイルがありませんでした。")
            return

        summaries = []
        seen_hashes = set()

        for file in sorted(files, key=lambda f: f.server_modified, reverse=True):
            path = file.path_display
            content = download_file(path)
            file_hash_value = file_hash(content)

            if file_hash_value in seen_hashes:
                continue
            seen_hashes.add(file_hash_value)

            summary = analyze_file(path)
            summaries.append(summary)

            if len(summaries) >= 3:  # 通知上限（過剰通知防止）
                break

        if summaries:
            now = datetime.datetime.now(pytz.timezone("Asia/Tokyo"))
            header = f"🧠最新解析結果（{now.strftime('%Y-%m-%d %H:%M')}）"
            result = "\n\n".join([header] + summaries)
            send_line_message(LINE_USER_ID, result)
        else:
            send_line_message(LINE_USER_ID, "新しいファイルはありませんでした。")

    except Exception as e:
        send_line_message(LINE_USER_ID, f"[全体エラー]: {str(e)}")