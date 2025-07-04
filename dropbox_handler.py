import dropbox
import hashlib
import os

# Dropboxアクセストークン（環境変数から取得）
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# ファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    result = dbx.files_list_folder(folder_path)
    return result.entries

# ファイルをダウンロード（バイナリ）
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# ハッシュ計算（重複判定用）
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# ファイル削除
def delete_file(path):
    dbx.files_delete_v2(path)
    print(f"✅ 削除済み: {path}")