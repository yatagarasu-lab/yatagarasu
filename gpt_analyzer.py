# gpt_analyzer.py

import os
import dropbox
from dropbox.files import FileMetadata
from openai import OpenAI
from utils.line_notify import send_line_message
from utils.file_utils import (
    list_files,
    download_file,
    file_hash,
    detect_file_type
)
from utils.image_ocr import extract_text_from_image_bytes
from dotenv import load_dotenv

load_dotenv()

# Dropbox認証情報（リフレッシュトークン方式）
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 4096))

# LINE通知用ユーザーID
LINE_USER_ID = os.getenv("LINE_USER_ID")

# GPT初期化
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_dropbox_client():
    """リフレッシュトークンからDropboxクライアントを生成"""
    oauth_result = dropbox.DropboxOAuth2FlowNoRedirect(
        consumer_key=DROPBOX_APP_KEY,
        consumer_secret=DROPBOX_APP_SECRET,
        token_access_type="offline"
    )
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )
    return dbx

def analyze_file(path, content, file_type):
    """ファイルの種類に応じて解析"""
    if file_type == "text":
        return analyze_text_content(path, content)
    elif file_type == "image":
        text = extract_text_from_image_bytes(content)
        return analyze_text_content(path + "（画像OCR）", text)
    else:
        return f"{path}: 対応していないファイル形式（{file_type}）"

def analyze_text_content(path, text):
    """テキストデータをGPTで要約解析"""
    if not text.strip():
        return f"{path}: 空のファイルでした。"

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "以下のテキストを要約してください。重要なキーワードや内容も抽出してください。"},
                {"role": "user", "content": text[:MAX_TOKENS]}
            ]
        )
        summary = response.choices[0].message.content
        return f"【{path} の解析結果】\n{summary}"
    except Exception as e:
        return f"{path} の解析中にエラー: {e}"

def analyze_dropbox_and_notify():
    """Dropboxフォルダ内のファイルを解析し、LINEに通知"""
    dbx = get_dropbox_client()
    folder_path = "/Apps/slot-data-analyzer"

    files = list_files(folder_path)
    if not files:
        send_line_message("Dropboxに解析対象のファイルがありません。", LINE_USER_ID)
        return

    results = []
    seen_hashes = set()

    for file in files:
        if isinstance(file, FileMetadata):
            path = file.path_display
            content = download_file(path)
            if content is None:
                continue

            hash_val = file_hash(content)
            if hash_val in seen_hashes:
                continue  # 重複ファイルはスキップ
            seen_hashes.add(hash_val)

            file_type = detect_file_type(path, content)
            result = analyze_file(path, content, file_type)
            results.append(result)

    final_message = "\n\n".join(results) if results else "有効なファイルが見つかりませんでした。"
    send_line_message(final_message, LINE_USER_ID)