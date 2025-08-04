import os
import dropbox
from dropbox.files import FileMetadata
from services.gpt_summarizer import summarize_text

# Dropboxのトークン情報を環境変数から取得
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")

# Dropboxインスタンスを返す
def get_dropbox_client():
    if not all([DROPBOX_REFRESH_TOKEN, DROPBOX_CLIENT_ID, DROPBOX_CLIENT_SECRET]):
        raise ValueError("Dropboxの認証情報が不足しています。")
    
    return dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_CLIENT_ID,
        app_secret=DROPBOX_CLIENT_SECRET
    )

# Dropbox内のファイルを一覧取得（指定なし → 全体）
def list_dropbox_files(folder_path: str = "") -> list:
    dbx = get_dropbox_client()
    files = []

    try:
        result = dbx.files_list_folder(folder_path)
        files.extend(result.entries)
        while result.has_more:
            result = dbx.files_list_folder_continue(result.cursor)
            files.extend(result.entries)
    except Exception as e:
        print(f"[Dropboxファイル一覧取得エラー] {str(e)}")

    return files

# ファイルをダウンロードしてテキストとして返す
def download_file_as_text(file_path: str) -> str:
    dbx = get_dropbox_client()
    try:
        metadata, res = dbx.files_download(file_path)
        content = res.content.decode("utf-8")
        return content
    except Exception as e:
        print(f"[Dropboxファイルダウンロードエラー] {str(e)}")
        return ""

# 指定ファイルの要約を実行し返す
def summarize_dropbox_file(file_path: str) -> str:
    content = download_file_as_text(file_path)
    if content:
        return summarize_text(content)
    else:
        return "ファイル読み込みに失敗しました。"

# 全ファイルの重複チェック（内容ハッシュベース）
def find_duplicate_files(folder_path: str = ""):
    import hashlib
    dbx = get_dropbox_client()
    hash_map = {}
    duplicates = []

    for entry in list_dropbox_files(folder_path):
        if isinstance(entry, FileMetadata):
            path = entry.path_display
            try:
                _, res = dbx.files_download(path)
                content = res.content
                hash_val = hashlib.sha256(content).hexdigest()

                if hash_val in hash_map:
                    print(f"[重複ファイル] {path} == {hash_map[hash_val]}")
                    duplicates.append((path, hash_map[hash_val]))
                else:
                    hash_map[hash_val] = path
            except Exception as e:
                print(f"[重複チェック中エラー] {str(e)}")
    return duplicates