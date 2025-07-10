import hashlib
import dropbox
from dropbox.files import WriteMode

from dropbox_token_refresher import get_dropbox_access_token

# Dropbox接続
def get_dropbox_client():
    token = get_dropbox_access_token()
    return dropbox.Dropbox(token)

# ファイル一覧取得（指定フォルダ以下）
def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    result = dbx.files_list_folder(folder_path, recursive=True)
    files = result.entries
    while result.has_more:
        result = dbx.files_list_folder_continue(result.cursor)
        files.extend(result.entries)
    return files

# ファイルのダウンロード（バイナリ取得）
def download_file(path):
    dbx = get_dropbox_client()
    metadata, res = dbx.files_download(path)
    return res.content

# ファイルのアップロード
def upload_file(file_bytes, dropbox_path):
    dbx = get_dropbox_client()
    dbx.files_upload(file_bytes, dropbox_path, mode=WriteMode("overwrite"))

# ファイル削除
def delete_file(path):
    dbx = get_dropbox_client()
    dbx.files_delete_v2(path)

# 内容ハッシュ生成
def file_hash(data):
    return hashlib.sha256(data).hexdigest()

# 重複ファイルチェック（同一内容のファイルパス一覧を返す）
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    hash_map = {}
    duplicates = []

    for file in list_files(folder_path):
        if isinstance(file, dropbox.files.FileMetadata):
            path = file.path_display
            content = download_file(path)
            h = file_hash(content)
            if h in hash_map:
                duplicates.append((path, hash_map[h]))
            else:
                hash_map[h] = path
    return duplicates