import os
import dropbox
import openai
import hashlib
from linebot import LineBotApi
from linebot.models import TextSendMessage
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# ===== 環境変数 =====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# ===== Dropbox OAuth2セッション作成（リフレッシュトークン対応） =====
def get_dropbox_client():
    oauth_result = dropbox.oauth.DropboxOAuth2FlowNoRedirect(
        consumer_key=DROPBOX_APP_KEY,
        consumer_secret=DROPBOX_APP_SECRET,
        token_access_type="offline"
    )
    dbx = dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )
    return dbx

# ===== ファイル一覧取得 =====
def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    files = []
    result = dbx.files_list_folder(folder_path)
    files.extend(result.entries)
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        files.extend(result.entries)
    return files

# ===== ファイルダウンロード（中身取得） =====
def download_file(path):
    dbx = get_dropbox_client()
    _, res = dbx.files_download(path)
    return res.content.decode("utf-8", errors="ignore")

# ===== GPT解析（要約・通知向けに軽量化） =====
def analyze_with_gpt(text):
    prompt = f"次の内容を簡潔に要約してください：\n\n{text[:3000]}"  # 軽量：3000文字以内
    response = openai.ChatCompletion.create(
        model="gpt-4o",  # または gpt-3.5-turbo
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_tokens=300
    )
    return response.choices[0].message.content.strip()

# ===== 内容の重複チェック用ハッシュ =====
def file_hash(text):
    return hashlib.md5(text.encode("utf-8")).hexdigest()

# ===== メイン処理（Dropbox→GPT→LINE通知） =====
def analyze_dropbox_and_notify():
    files = list_files()
    hash_map = {}
    summaries = []

    for file in tqdm(files, desc="解析中"):
        path = file.path_display
        if not path.endswith((".txt", ".log", ".csv")):
            continue  # テキスト系だけ対象に軽量化

        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複スキップ: {path}")
            continue

        summary = analyze_with_gpt(content)
        summaries.append(f"📂 {os.path.basename(path)}\n{summary}")
        hash_map[hash_value] = path

    # ===== 結果をLINE通知（最新5件のみ） =====
    if summaries:
        final_text = "\n\n".join(summaries[-5:])
    else:
        final_text = "新規解析対象ファイルがありませんでした。"

    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=final_text)
    )