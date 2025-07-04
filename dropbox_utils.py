# dropbox_utils.py
import dropbox
import hashlib
from dropbox_auth import get_dropbox_access_token

# Dropbox接続
def get_dbx():
    return dropbox.Dropbox(oauth2_access_token=get_dropbox_access_token())

# ファイル一覧を取得
def list_files(folder_path):
    dbx = get_dbx()
    try:
        result = dbx.files_list_folder(folder_path)
        files = result.entries
        while result.has_more:
            result = dbx.files_list_folder_continue(result.cursor)
            files.extend(result.entries)
        return files
    except dropbox.exceptions.ApiError as e:
        print(f"❌ Dropbox API エラー: {e}")
        return []

# ファイルをダウンロード
def download_file(path):
    dbx = get_dbx()
    _, res = dbx.files_download(path)
    return res.content

# ファイルをアップロード（テキストやZIPに使用）
def upload_file(content, dropbox_path):
    dbx = get_dbx()
    dbx.files_upload(content, dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

# ハッシュで内容の重複をチェック
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# ファイルを削除
def delete_file(path):
    dbx = get_dbx()
    dbx.files_delete_v2(path)

# 重複ファイルの検出と削除（同じ中身が複数ある場合は1つ残して削除）
def find_duplicates_and_delete(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display

        # 処理済みZIPファイルなどは除外（必要に応じて調整）
        if path.startswith(folder_path + "/processed") or path.endswith(".zip"):
            continue

        try:
            content = download_file(path)
            hash_value = file_hash(content)

            if hash_value in hash_map:
                print(f"⚠️ 重複ファイル削除: {path}（同一: {hash_map[hash_value]}）")
                delete_file(path)
            else:
                hash_map[hash_value] = path
        except Exception as e:
            print(f"❌ 重複チェック中エラー: {e}")