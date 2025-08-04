# dropbox_handler.py

import dropbox
import hashlib
from dropbox.exceptions import AuthError, ApiError
import os

# Dropbox初期化
dbx = dropbox.Dropbox(oauth2_refresh_token=os.getenv("DROPBOX_REFRESH_TOKEN"),
                      app_key=os.getenv("DROPBOX_CLIENT_ID"),
                      app_secret=os.getenv("DROPBOX_CLIENT_SECRET"))

# ファイルのハッシュ生成（重複判定用）
def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

# Dropboxのファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except ApiError as e:
        print(f"[DROPBOX ERROR] ファイル一覧取得失敗: {e}")
        return []

# 単一ファイルのダウンロード
def download_file(path: str) -> bytes:
    try:
        _, res = dbx.files_download(path)
        return res.content
    except ApiError as e:
        print(f"[DROPBOX ERROR] ファイルダウンロード失敗: {e}")
        return b""

# 新規ファイルだけを抽出（重複回避）
def get_new_files(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    new_files = []

    for file in files:
        if not isinstance(file, dropbox.files.FileMetadata):
            continue

        path = file.path_display
        content = download_file(path)
        h = file_hash(content)

        if h not in hash_map:
            hash_map[h] = path
            new_files.append((file.name, content))
        else:
            print(f"[INFO] 重複ファイルスキップ: {file.name}")

    return new_files