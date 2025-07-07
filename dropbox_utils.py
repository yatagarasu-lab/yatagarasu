import os
import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox.exceptions import AuthError

# 環境変数からアクセストークンとリフレッシュトークンを取得
APP_KEY = os.getenv("DROPBOX_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# Dropbox API クライアント（リフレッシュトークンで認証）
dbx = dropbox.Dropbox(
    oauth2_refresh_token=REFRESH_TOKEN,
    app_key=APP_KEY,
    app_secret=APP_SECRET
)

FOLDER_PATH = "/Apps/slot-data-analyzer"

def list_files(folder_path=FOLDER_PATH):
    """Dropboxフォルダ内のファイル一覧を取得"""
    try:
        res = dbx.files_list_folder(folder_path)
        return res.entries
    except AuthError as e:
        print("Dropbox認証エラー:", e)
        return []

def download_file(path):
    """Dropboxからファイルをダウンロード"""
    try:
        _, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"ファイルダウンロードエラー: {e}")
        return None

def file_hash(data):
    """ファイル内容のハッシュ値を取得（重複判定用）"""
    import hashlib
    return hashlib.md5(data).hexdigest()

def find_duplicates(folder_path=FOLDER_PATH):
    """Dropboxフォルダ内の重複ファイルを検出"""
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
            # dbx.files_delete_v2(path)  # ←自動削除するならこの行を有効に
        else:
            hash_map[hash_value] = path