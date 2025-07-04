import dropbox
import hashlib
import os

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_files(folder_path):
    """Dropboxフォルダ内のファイル一覧を取得"""
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"⚠️ ファイル一覧取得失敗: {e}")
        return []

def download_file(path):
    """Dropbox上のファイルをバイナリでダウンロード"""
    try:
        _, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"⚠️ ファイルダウンロード失敗: {e}")
        return None

def file_hash(content):
    """バイナリ内容のSHA256ハッシュを計算"""
    return hashlib.sha256(content).hexdigest()

def delete_file(path):
    """Dropbox上のファイルを削除"""
    try:
        dbx.files_delete_v2(path)
        print(f"🗑️ 削除成功: {path}")
    except Exception as e:
        print(f"⚠️ 削除失敗: {e}")

def upload_file(file_bytes: bytes, dropbox_path: str):
    """バイナリデータをDropboxにアップロード"""
    try:
        dbx.files_upload(file_bytes, dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
        print(f"✅ アップロード成功: {dropbox_path}")
    except Exception as e:
        print(f"⚠️ アップロード失敗: {e}")