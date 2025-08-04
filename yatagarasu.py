import openai
import dropbox

# 環境変数からAPIキーなどを取得
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# GPT API初期化
openai.api_key = OPENAI_API_KEY

# Dropbox API初期化（refresh_token対応）
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox import Dropbox

dbx = Dropbox(
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET,
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
)

# ファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    result = dbx.files_list_folder(folder_path)
    return result.entries

# ファイル内容を読み込む（バイナリ → テキスト変換）
def download_and_read_text(path):
    _, res = dbx.files_download(path)
    content = res.content.decode('utf-8', errors='ignore')
    return content

# GPTに解析依頼
def analyze_text_with_gpt(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたはスロット設定解析の専門家です。"},
            {"role": "user", "content": f"以下のデータを解析してください：\n\n{text}"}
        ]
    )
    return response.choices[0].message.content.strip()

# メイン処理：最新ファイルを解析
def analyze_latest_file(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    if not files:
        return "解析対象ファイルが見つかりませんでした。"

    latest_file = sorted(files, key=lambda x: x.server_modified, reverse=True)[0]
    text = download_and_read_text(latest_file.path_display)
    analysis_result = analyze_text_with_gpt(text)

    return f"✅ 最新ファイル名: {latest_file.name}\n\n🧠 解析結果:\n{analysis_result}"
