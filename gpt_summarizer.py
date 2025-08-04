# gpt_summarizer.py（完全版）📄 Dropbox → GPT要約・重複判定付き
import hashlib
import os
import dropbox
import openai

# Dropbox API初期化
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_ACCESS_TYPE = "offline"
DROPBOX_ROOT_PATH = "/Apps/slot-data-analyzer"

# OpenAI APIキー
openai.api_key = os.getenv("OPENAI_API_KEY")

# アクセストークンの取得
def get_dropbox_client():
    if not (DROPBOX_REFRESH_TOKEN and DROPBOX_APP_KEY and DROPBOX_APP_SECRET):
        raise Exception("Dropboxの環境変数が設定されていません。")
    return dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )

# SHA256でハッシュ計算（重複検出用）
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# GPTによる要約処理
def summarize_with_gpt(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "ファイル内容を要約してください"},
            {"role": "user", "content": text}
        ],
        max_tokens=500
    )
    return response["choices"][0]["message"]["content"]

# Dropbox内の全ファイルを処理
def process_dropbox_files():
    dbx = get_dropbox_client()
    hash_map = {}
    processed_summaries = []

    for entry in dbx.files_list_folder(DROPBOX_ROOT_PATH).entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            path = entry.path_display
            _, res = dbx.files_download(path)
            content = res.content
            h = file_hash(content)

            if h in hash_map:
                print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[h]}）")
                dbx.files_delete_v2(path)  # 重複なら削除
                continue

            hash_map[h] = path

            try:
                decoded = content.decode("utf-8")
                summary = summarize_with_gpt(decoded)
                processed_summaries.append({
                    "path": path,
                    "summary": summary
                })
                print(f"✅ 要約完了: {path}")
            except Exception as e:
                print(f"❌ 要約失敗 {path}: {str(e)}")

    return processed_summaries