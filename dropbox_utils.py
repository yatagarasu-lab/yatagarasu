# dropbox_utils.py 🗂 Dropbox操作関連
import os
import dropbox
import hashlib

DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

def get_dropbox_client():
    if not all([DROPBOX_REFRESH_TOKEN, DROPBOX_APP_KEY, DROPBOX_APP_SECRET]):
        raise Exception("Dropboxの認証情報が不足しています")
    return dropbox.Dropbox(
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET,
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN
    )

def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    files = []
    try:
        result = dbx.files_list_folder(folder_path)
        files.extend(result.entries)
        while result.has_more:
            result = dbx.files_list_folder_continue(result.cursor)
            files.extend(result.entries)
    except Exception as e:
        print(f"❌ ファイル一覧取得エラー: {e}")
    return files

def download_file(path):
    dbx = get_dropbox_client()
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"❌ ファイルダウンロードエラー: {e}")
        return None

def delete_file(path):
    dbx = get_dropbox_client()
    try:
        dbx.files_delete_v2(path)
        print(f"🗑 削除完了: {path}")
    except Exception as e:
        print(f"❌ 削除エラー: {e}")

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def find_and_remove_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        if content is None:
            continue
        h = file_hash(content)

        if h in hash_map:
            print(f"⚠️ 重複検出: {path} == {hash_map[h]}")
            delete_file(path)
        else:
            hash_map[h] = path
