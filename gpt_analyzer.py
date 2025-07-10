# gpt_analyzer.py

import os
import dropbox
from dropbox.exceptions import AuthError
from openai import OpenAI
from utils.image_ocr import extract_text_from_image
from utils.line_notify import push_line_message
from utils.file_utils import list_files, download_file, is_image
from utils.token_refresher import refresh_dropbox_access_token

# OpenAI APIキーとモデル
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))

# Dropboxトークン（アクセストークンは毎回更新）
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

# 対象フォルダ（Dropbox）
TARGET_FOLDER = "/Apps/slot-data-analyzer"

# LINEユーザーID（Push先）
LINE_USER_ID = os.getenv("LINE_USER_ID")


def analyze_dropbox_and_notify():
    """Dropboxフォルダを解析してLINEに通知するメイン関数"""
    access_token = refresh_dropbox_access_token(DROPBOX_REFRESH_TOKEN, DROPBOX_APP_KEY, DROPBOX_APP_SECRET)
    dbx = dropbox.Dropbox(oauth2_access_token=access_token)

    try:
        files = list_files(TARGET_FOLDER, dbx)
        summaries = []

        for file in files:
            filename = file.name
            file_path = file.path_display
            file_bytes = download_file(file_path, dbx)

            # 画像 or テキストファイルかで分岐
            if is_image(filename):
                extracted_text = extract_text_from_image(file_bytes)
                content_for_gpt = f"画像ファイル「{filename}」から抽出されたテキスト:\n{extracted_text}"
            else:
                try:
                    content_for_gpt = file_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    content_for_gpt = "[非対応のファイル形式]"

            # GPTで要約
            summary = summarize_with_gpt(content_for_gpt)
            summaries.append(f"■{filename}:\n{summary.strip()}")

        # LINEへまとめて通知（長文は分割して送信）
        final_message = "\n\n".join(summaries)
        push_line_message(final_message, LINE_USER_ID)

    except AuthError as e:
        push_line_message(f"[Dropbox認証エラー]: {str(e)}", LINE_USER_ID)


def summarize_with_gpt(content: str) -> str:
    """OpenAI GPTを使って内容を要約"""
    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": "これはDropboxからのファイル内容です。要点を簡潔にまとめてください。"},
                {"role": "user", "content": content}
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.5,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"[GPT要約エラー]: {str(e)}"