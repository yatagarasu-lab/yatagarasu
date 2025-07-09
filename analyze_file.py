import os
import dropbox
import hashlib
import pytesseract
from PIL import Image
from io import BytesIO
import openai
import requests
from dotenv import load_dotenv
import json

load_dotenv()

# 環境変数の読み込み
DROPBOX_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"
LINE_USER_ID = os.getenv("LINE_USER_ID")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# OpenAI設定
openai.api_key = OPENAI_API_KEY

# Dropbox認証
auth_flow = dropbox.DropboxOAuth2FlowNoRedirect(DROPBOX_APP_KEY, consumer_secret=DROPBOX_APP_SECRET, token_access_type='offline')
dbx = dropbox.Dropbox(oauth2_refresh_token=DROPBOX_TOKEN, app_key=DROPBOX_APP_KEY, app_secret=DROPBOX_APP_SECRET)

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

def classify_file(content):
    try:
        image = Image.open(BytesIO(content))
        text = pytesseract.image_to_string(image, lang="jpn")
        return "画像", text
    except Exception:
        try:
            text = content.decode("utf-8")
            return "テキスト", text
        except:
            return "その他", "このファイルはテキストまたは画像として解析できませんでした。"

def summarize_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "以下のテキストを簡潔に要約してください。"},
                {"role": "user", "content": text[:4000]}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"要約に失敗しました: {str(e)}"

def send_line_message(user_id, message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": user_id,
        "messages": [{"type": "text", "text": message}]
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    return response.status_code, response.text

def analyze_dropbox_files():
    try:
        result = dbx.files_list_folder(DROPBOX_FOLDER_PATH)
    except Exception as e:
        print(f"Dropboxフォルダ取得失敗: {e}")
        return

    files = result.entries
    hash_map = {}

    for file in files:
        if not isinstance(file, dropbox.files.FileMetadata):
            continue

        path = file.path_display
        try:
            content = download_file(path)
            h = file_hash(content)
        except Exception as e:
            print(f"[⚠️] ファイルダウンロード失敗: {path}, 理由: {e}")
            continue

        if h in hash_map:
            print(f"[🗑] 重複検出: {path}（既に {hash_map[h]} と同一） → 削除")
            dbx.files_delete_v2(path)
            continue

        hash_map[h] = path
        file_type, raw_text = classify_file(content)
        summary = summarize_text(raw_text)

        message = f"[🗂] 新規ファイル解析完了\n📄種別: {file_type}\n📝要約:\n{summary}"
        print(message)
        send_line_message(LINE_USER_ID, message)

        try:
            new_path = f"{DROPBOX_FOLDER_PATH}/分類済/{file_type}/{file.name}"
            dbx.files_move_v2(path, new_path)
        except Exception as e:
            print(f"[⚠️] 分類フォルダ移動失敗: {e}")