import dropbox
import hashlib
import os

DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_files(folder_path="/Apps/slot-data-analyzer"):
    """フォルダ内のファイル一覧を取得"""
    result = dbx.files_list_folder(folder_path)
    return result.entries

def download_file(file_path):
    """Dropboxからファイルをダウンロード"""
    metadata, res = dbx.files_download(file_path)
    return res.content

def file_hash(content):
    """ファイルのSHA256ハッシュを計算"""
    return hashlib.sha256(content).hexdigest()

def delete_file(file_path):
    """Dropboxからファイルを削除"""
    dbx.files_delete_v2(file_path)
    print(f"🗑️ 削除しました: {file_path}")