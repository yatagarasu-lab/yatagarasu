import os
import dropbox
import hashlib
from openai import OpenAI
from linebot import LineBotApi
from linebot.models import TextSendMessage
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# 環境変数
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# LINE 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Dropbox 初期化（リフレッシュトークン使用）
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET,
)

# OpenAI 初期化
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Dropboxからファイル一覧取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

# ファイルの中身をダウンロード
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content.decode("utf-8", errors="ignore")

# ファイル内容のハッシュを取得（重複判定用）
def file_hash(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

# GPTでファイル内容を要約
def summarize_content(content):
    prompt = f"以下の内容を要約してください（日本語で簡潔に）:\n\n{content[:3000]}"
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT要約失敗] {str(e)}"

# LINEに通知
def send_to_line(message):
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))

# メイン処理（GPT解析＋通知＋重複ファイル削除）
def analyze_dropbox_and_notify():
    folder = "/Apps/slot-data-analyzer"
    files = list_files(folder)
    hash_map = {}

    if not files:
        send_to_line("Dropbox内に解析可能なファイルがありません。")
        return

    for file in tqdm(files, desc="解析中"):
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        # 重複ファイルチェック
        if hash_value in hash_map:
            dbx.files_delete_v2(path)
            print(f"✅ 重複削除: {path}")
            continue

        hash_map[hash_value] = path
        summary = summarize_content(content)

        # 通知用メッセージ生成
        filename = os.path.basename(path)
        message = f"📄 {filename} の解析結果:\n\n{summary}"
        send_to_line(message)