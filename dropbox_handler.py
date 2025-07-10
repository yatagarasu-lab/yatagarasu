import os
import dropbox

# Dropboxクライアント（リフレッシュトークン対応）
dbx = dropbox.Dropbox(
    oauth2_refresh_token=os.getenv("DROPBOX_REFRESH_TOKEN"),
    app_key=os.getenv("DROPBOX_APP_KEY"),
    app_secret=os.getenv("DROPBOX_APP_SECRET")
)

def list_files(folder_path="/Apps/slot-data-analyzer"):
    """Dropboxフォルダ内のファイル一覧を取得"""
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except dropbox.exceptions.ApiError as e:
        print(f"[エラー] ファイル一覧取得失敗: {e}")
        return []

def download_file(path):
    """Dropboxからファイルをダウンロードしてバイナリを返す"""
    try:
        _, res = dbx.files_download(path)
        return res.content
    except dropbox.exceptions.HttpError as e:
        print(f"[エラー] ファイルダウンロード失敗: {e}")
        return b""

def delete_file(path):
    """Dropboxの指定ファイルを削除"""
    try:
        dbx.files_delete_v2(path)
        print(f"[削除] 重複ファイル削除: {path}")
    except dropbox.exceptions.ApiError as e:
        print(f"[削除失敗] {path}: {e}")