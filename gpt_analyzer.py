import dropbox
import hashlib
import os
import openai
from linebot import LineBotApi
from linebot.models import TextSendMessage
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_fixed

# LINE設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# OpenAI設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# Dropboxリフレッシュトークン認証
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")


def get_dropbox_client():
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox.dropbox_client import Dropbox

    # リフレッシュトークンからアクセストークン生成
    oauth_result = dropbox.DropboxOAuth2FlowNoRedirect(
        consumer_key=DROPBOX_APP_KEY,
        consumer_secret=DROPBOX_APP_SECRET,
        token_access_type='offline'
    )
    dbx = Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )
    return dbx


def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    result = dbx.files_list_folder(folder_path)
    return result.entries


def download_file(path: str) -> bytes:
    dbx = get_dropbox_client()
    metadata, res = dbx.files_download(path)
    return res.content


def summarize_text(text: str) -> str:
    """GPTで要約"""
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "以下の情報を要約し、重要な点を簡潔にまとめてください。"},
            {"role": "user", "content": text}
        ],
        max_tokens=800
    )
    return response["choices"][0]["message"]["content"].strip()


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def analyze_dropbox_and_notify():
    dbx = get_dropbox_client()
    files = list_files()

    hash_map = {}
    latest_text = None
    latest_name = None

    for file in sorted(files, key=lambda f: f.client_modified, reverse=True):
        if not file.name.lower().endswith((".txt", ".md", ".csv")):
            continue

        content = download_file(file.path_display)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            dbx.files_delete_v2(file.path_display)
            continue

        hash_map[hash_value] = file.name

        # 先頭の1ファイルだけを解析
        latest_text = content.decode("utf-8", errors="ignore")
        latest_name = file.name
        break

    if latest_text:
        summary = summarize_text(latest_text)
        message = f"📄 {latest_name} を解析しました：\n\n{summary}"
    else:
        message = "解析対象の新しいテキストファイルが見つかりませんでした。"

    # LINEに通知
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=message)
    )