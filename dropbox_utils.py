import os
import dropbox
import hashlib

# Dropbox APIのリフレッシュトークン設定
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

# Dropboxへの接続
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

# 対象フォルダ（Apps配下）
FOLDER_PATH = "/slot-data-analyzer"

# ファイル一覧取得
def list_files(folder_path=FOLDER_PATH):
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"❌ ファイル一覧取得エラー: {e}")
        return []

# ファイルダウンロード
def download_file(path):
    try:
        _, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"❌ ダウンロードエラー: {e}")
        return None

# ハッシュ生成（重複チェック用）
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# 重複ファイルの検出と処理
def find_duplicates(folder_path=FOLDER_PATH):
    print("🔍 Dropbox重複チェック開始...")
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        if content is None:
            continue

        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # dbx.files_delete_v2(path)  # 本番ではコメント解除
        else:
            hash_map[hash_value] = path

    print("✅ 重複チェック完了")