import os
import hashlib
import dropbox

# Dropbox APIアクセストークン（.envから読み込む想定）
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# フォルダパス（固定でApps/slot-data-analyzerに）
FOLDER_PATH = "/Apps/slot-data-analyzer"

def list_files(folder_path=FOLDER_PATH):
    """Dropboxフォルダ内のファイル一覧を取得"""
    result = dbx.files_list_folder(folder_path)
    return result.entries

def download_file(path):
    """指定ファイルの中身を取得（バイナリ）"""
    metadata, res = dbx.files_download(path)
    return res.content

def file_hash(content):
    """ファイル内容からハッシュを生成（重複検出用）"""
    return hashlib.sha256(content).hexdigest()

def delete_file(path):
    """ファイルをDropboxから削除"""
    dbx.files_delete_v2(path)