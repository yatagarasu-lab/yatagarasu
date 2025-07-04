import os
import dropbox
import hashlib

DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

def list_files(folder_path):
    """Dropboxフォルダ内のファイル一覧を取得"""
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"📂 ファイル一覧取得エラー: {e}")
        return []

def download_file(path):
    """Dropboxからファイルをバイナリで取得"""
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"⬇️ ファイルダウンロードエラー: {e}")
        return None

def upload_file(path, content):
    """Dropboxにファイルをアップロード"""
    try:
        dbx.files_upload(content, path, mode=dropbox.files.WriteMode.overwrite)
        print(f"✅ アップロード成功: {path}")
    except Exception as e:
        print(f"⬆️ アップロード失敗: {e}")

def delete_file(path):
    """Dropboxからファイルを削除"""
    try:
        dbx.files_delete_v2(path)
        print(f"🗑️ 削除成功: {path}")
    except Exception as e:
        print(f"🗑️ 削除失敗: {e}")

def file_hash(content):
    """ファイル内容からSHA256ハッシュを生成"""
    return hashlib.sha256(content).hexdigest()