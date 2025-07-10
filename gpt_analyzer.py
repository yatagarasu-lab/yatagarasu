import os
import io
import dropbox
from dropbox.files import FileMetadata
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox.exceptions import AuthError
from openai import OpenAI
from linebot import LineBotApi
from linebot.models import TextSendMessage
import hashlib
import time
import threading

# 環境変数の取得
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Dropbox & LINE初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def get_dropbox_client():
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect, DropboxOAuth2Session
    oauth_session = DropboxOAuth2Session(
        consumer_key=DROPBOX_APP_KEY,
        consumer_secret=DROPBOX_APP_SECRET,
        refresh_token=DROPBOX_REFRESH_TOKEN
    )
    return dropbox.Dropbox(oauth2_access_token=oauth_session.token)

dbx = get_dropbox_client()
openai = OpenAI(api_key=OPENAI_API_KEY)


# ==============================
# ユーティリティ関数
# ==============================

def file_hash(binary):
    return hashlib.md5(binary).hexdigest()

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return [entry for entry in res.entries if isinstance(entry, FileMetadata)]

def send_line_notification(text):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
    except Exception as e:
        print("LINE送信エラー:", e)

def summarize_text(content):
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "これはDropboxに保存されたパチスロ設定やイベントに関するデータです。内容を簡潔に要約してください。"},
                {"role": "user", "content": content}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"要約中にエラー: {e}"

# ==============================
# メイン解析関数
# ==============================

def analyze_dropbox_and_notify():
    folder_path = "/Apps/slot-data-analyzer"
    files = list_files(folder_path)

    hash_map = {}
    latest_text = None
    latest_path = None

    for file in sorted(files, key=lambda x: x.server_modified, reverse=True):
        path = file.path_display
        content = download_file(path)
        hash_val = file_hash(content)

        if hash_val in hash_map:
            dbx.files_delete_v2(path)  # 重複ファイルを削除
        else:
            hash_map[hash_val] = path
            if latest_text is None:
                latest_text = content.decode("utf-8", errors="ignore")
                latest_path = path

    if latest_text:
        summary = summarize_text(latest_text)
        message = f"🧠最新ファイル解析結果（{os.path.basename(latest_path)}）:\n{summary}"
    else:
        message = "Dropbox内に解析対象の新しいファイルがありませんでした。"

    send_line_notification(message)