import dropbox
import hashlib
import os

# Dropboxアクセストークンの読み込み
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def upload_file(file_path, dropbox_path):
    """ローカルファイルをDropboxにアップロード"""
    with open(file_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)

def upload_bytes(content, dropbox_path):
    """バイナリデータをDropboxにアップロード"""
    dbx.files_upload(content, dropbox_path, mode=dropbox.files.WriteMode.overwrite)

def download_file(dropbox_path):
    """Dropboxからファイルをダウンロード"""
    metadata, res = dbx.files_download(dropbox_path)
    return res.content

def list_files(folder_path="/Apps/slot-data-analyzer"):
    """指定フォルダ内のファイルを一覧取得"""
    result = dbx.files_list_folder(folder_path)
    return result.entries

def delete_file(dropbox_path):
    """Dropboxのファイルを削除"""
    dbx.files_delete_v2(dropbox_path)

def file_hash(content):
    """ファイル内容からSHA-256のハッシュを生成"""
    return hashlib.sha256(content).hexdigest()