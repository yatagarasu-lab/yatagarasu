import dropbox
import os
import hashlib
from openai import OpenAI
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 環境変数からトークン取得
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# LINE送信用
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# OpenAIクライアント初期化
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Dropboxに接続（リフレッシュトークン方式）
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox import DropboxOAuth2FlowNoRedirect, Dropbox

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

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def analyze_with_gpt(content: bytes) -> str:
    try:
        result = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "これはDropboxに追加されたファイルの自動解析です。重複チェックと内容要約を行ってください。"},
                {"role": "user", "content": content.decode('utf-8', errors='ignore')[:3000]}  # 安全対策で先頭3KBのみ渡す
            ]
        )
        return result.choices[0].message.content.strip()
    except Exception as e:
        return f"[解析エラー] {str(e)}"

def notify_line(message: str):
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=message)
    )

def process_dropbox_changes():
    try:
        files = list_files()
        hash_map = {}

        for file in files:
            path = file.path_display
            content = download_file(path)
            h = file_hash(content)

            if h in hash_map:
                print(f"[重複] {path}（同一: {hash_map[h]}）→ スキップ")
                continue

            hash_map[h] = path
            print(f"[解析対象] {path}")
            result = analyze_with_gpt(content)
            notify_line(f"📂 新ファイル解析結果\n\n📎 {path}\n🧠 GPT解析：\n{result}")

    except Exception as e:
        print(f"[全体エラー] {e}")
        notify_line(f"[エラー発生] {str(e)}")