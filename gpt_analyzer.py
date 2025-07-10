import os
import dropbox
import hashlib
import io
import easyocr
import openai
from PIL import Image
from dropbox.files import FileMetadata
from line_notify import send_line_message

# 環境変数
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 初期設定
openai.api_key = OPENAI_API_KEY

# EasyOCR初期化（日本語+英語）
ocr_reader = easyocr.Reader(["ja", "en"], gpu=False)

def get_dropbox_access_token():
    import requests
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "grant_type": "refresh_token",
        "client_id": DROPBOX_APP_KEY,
        "client_secret": DROPBOX_APP_SECRET
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

def connect_dropbox():
    token = get_dropbox_access_token()
    return dropbox.Dropbox(oauth2_access_token=token)

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def analyze_dropbox_and_notify():
    dbx = connect_dropbox()
    folder_path = "/Apps/slot-data-analyzer"
    files = dbx.files_list_folder(folder_path).entries

    hash_map = {}
    for file in sorted(files, key=lambda x: x.server_modified, reverse=True):
        if not isinstance(file, FileMetadata):
            continue

        path = file.path_display
        _, ext = os.path.splitext(path.lower())
        content = dbx.files_download(path)[1].content

        hash_value = file_hash(content)
        if hash_value in hash_map:
            continue
        hash_map[hash_value] = path

        # 画像 or テキストの処理
        if ext in [".jpg", ".jpeg", ".png"]:
            text = ocr_image(content)
        elif ext in [".txt"]:
            text = content.decode("utf-8")
        else:
            continue

        summary = summarize_with_gpt(text)
        send_line_message(summary)

def ocr_image(content):
    try:
        image = Image.open(io.BytesIO(content)).convert("RGB")
        result = ocr_reader.readtext(np.array(image), detail=0)
        return "\n".join(result)
    except Exception as e:
        return f"OCRエラー: {e}"

def summarize_with_gpt(text):
    try:
        prompt = f"以下の情報を要約してください：\n{text[:2000]}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.5,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"要約エラー: {e}"