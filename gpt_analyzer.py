import os
import dropbox
import openai
from datetime import datetime, timedelta
from linebot import LineBotApi
from linebot.models import TextSendMessage
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox.files import FileMetadata
import hashlib

# ==== 環境変数読み込み ====
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# ==== 初期化 ====
openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)


def get_dropbox_access_token():
    """リフレッシュトークンを使ってアクセストークンを取得"""
    import requests
    response = requests.post(
        "https://api.dropbox.com/oauth2/token",
        auth=(DROPBOX_APP_KEY, DROPBOX_APP_SECRET),
        data={
            "grant_type": "refresh_token",
            "refresh_token": DROPBOX_REFRESH_TOKEN
        },
    )
    return response.json()["access_token"]


def list_recent_files(dbx, folder_path="/Apps/slot-data-analyzer", minutes=10):
    """直近N分以内に更新されたファイル一覧"""
    recent_files = []
    now = datetime.utcnow()
    time_threshold = now - timedelta(minutes=minutes)

    for entry in dbx.files_list_folder(folder_path).entries:
        if isinstance(entry, FileMetadata):
            if entry.server_modified > time_threshold:
                recent_files.append(entry)
    return recent_files


def download_file(dbx, path):
    """Dropboxからファイルをダウンロード"""
    metadata, res = dbx.files_download(path)
    return res.content


def summarize_with_gpt(content_bytes, filename):
    """GPTで内容要約（テキスト or 画像 or バイナリ）"""
    try:
        text = content_bytes.decode("utf-8")
    except Exception:
        text = f"{filename} を受信しました（内容の解析は別途対応中）"
    return f"📝 {filename} の要約\n\n{text[:300]}..."


def push_notification(message):
    """LINEへPush通知"""
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))


def analyze_dropbox_and_notify():
    """Dropboxの最新ファイルを解析してLINEへ通知"""
    token = get_dropbox_access_token()
    dbx = dropbox.Dropbox(token)

    recent_files = list_recent_files(dbx)
    if not recent_files:
        push_notification("📂 新しいファイルは見つかりませんでした。")
        return

    for file in recent_files:
        content = download_file(dbx, file.path_display)
        summary = summarize_with_gpt(content, file.name)
        push_notification(summary)