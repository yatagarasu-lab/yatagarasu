import os
import dropbox
import hashlib

# 環境変数からDropboxのリフレッシュトークンとApp Key/Secretを取得
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
FOLDER_PATH = "/Apps/slot-data-analyzer"

# Dropboxクライアントの初期化（リフレッシュトークン方式）
def create_dropbox_client():
    if not DROPBOX_REFRESH_TOKEN or not DROPBOX_APP_KEY or not DROPBOX_APP_SECRET:
        raise ValueError("Dropboxの環境変数が正しく設定されていません")
    
    return dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )

dbx = create_dropbox_client()

# フォルダ内のファイル一覧を取得
def list_files(folder_path=FOLDER_PATH):
    try:
        res = dbx.files_list_folder(folder_path)
        return res.entries
    except Exception as e:
        print(f"Dropboxフォルダ一覧取得エラー: {e}")
        return []

# 指定パスのファイルをダウンロード
def download_file(path):
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"Dropboxファイルダウンロードエラー: {e}")
        return None

# ファイルのハッシュ値を計算（重複判定用）
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# 重複ファイルを検出・削除（任意で有効化）
def find_duplicates(folder_path=FOLDER_PATH):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        if content is None:
            continue
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"✅ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # 削除したい場合はこちらを有効化
            # dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path