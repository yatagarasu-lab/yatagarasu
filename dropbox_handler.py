import dropbox
import hashlib
import os

# Dropboxクライアント初期化
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_files(folder_path="/Apps/slot-data-analyzer"):
    """指定フォルダ内のファイル一覧を取得"""
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"📁 フォルダ一覧取得失敗: {e}")
        return []

def download_file(path):
    """Dropboxからファイルをバイナリでダウンロード"""
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"⬇️ ダウンロード失敗（{path}）: {e}")
        return None

def file_hash(content):
    """ファイルのSHA256ハッシュを計算"""
    return hashlib.sha256(content).hexdigest()

def delete_file(path):
    """Dropbox上のファイルを削除"""
    try:
        dbx.files_delete_v2(path)
        print(f"🗑️ 削除成功: {path}")
    except Exception as e:
        print(f"⚠️ 削除失敗（{path}）: {e}")