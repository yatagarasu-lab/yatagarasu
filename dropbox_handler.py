import dropbox
import os
import hashlib

DROPBOX_ACCESS_TOKEN = os.environ["DROPBOX_ACCESS_TOKEN"]
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def upload_file(path, binary_content):
    """Dropboxにバイナリファイルをアップロード"""
    dbx.files_upload(binary_content, path, mode=dropbox.files.WriteMode("overwrite"))

def upload_text(path, text):
    """Dropboxにテキストファイルをアップロード"""
    dbx.files_upload(text.encode("utf-8"), path, mode=dropbox.files.WriteMode("overwrite"))

def list_files(folder_path):
    """指定フォルダ内のファイル一覧取得"""
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    """Dropboxからファイルをダウンロード"""
    _, res = dbx.files_download(path)
    return res.content

def file_hash(content):
    """バイナリコンテンツのハッシュ値を取得"""
    return hashlib.md5(content).hexdigest()

def delete_file(path):
    """Dropboxのファイルを削除"""
    dbx.files_delete_v2(path)