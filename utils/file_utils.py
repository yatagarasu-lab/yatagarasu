import hashlib
from dropbox import Dropbox
from dropbox.files import WriteMode
import os

DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

from utils.dropbox_auth import get_dropbox_client  # 認証モジュールから取得（事前に作成済み）

def file_hash(content: bytes) -> str:
    """ファイル内容からSHA-256ハッシュを生成"""
    return hashlib.sha256(content).hexdigest()

def find_and_remove_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """Dropboxフォルダ内の重複ファイルを検出し、自動削除"""
    dbx = get_dropbox_client()
    hash_map = {}

    try:
        result = dbx.files_list_folder(folder_path, recursive=True)
        entries = result.entries

        while result.has_more:
            result = dbx.files_list_folder_continue(result.cursor)
            entries.extend(result.entries)

        for file in entries:
            if isinstance(file, dropbox.files.FileMetadata):
                path = file.path_display
                content = dbx.files_download(path)[1].content
                hash_value = file_hash(content)

                if hash_value in hash_map:
                    print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
                    dbx.files_delete_v2(path)
                else:
                    hash_map[hash_value] = path

    except Exception as e:
        print(f"重複検出処理中にエラー: {e}")
