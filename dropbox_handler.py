import dropbox
import os
import hashlib

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def download_file(path: str) -> bytes:
    """
    指定された Dropbox パスからファイルをダウンロードし、バイトデータで返す
    """
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"❌ Dropboxダウンロードエラー: {e}")
        return b''

def list_files(folder_path: str = "/Apps/slot-data-analyzer") -> list:
    """
    Dropboxフォルダ内のファイル一覧を取得する
    """
    try:
        res = dbx.files_list_folder(folder_path)
        return res.entries
    except Exception as e:
        print(f"❌ Dropboxファイル一覧取得エラー: {e}")
        return []

def file_hash(content: bytes) -> str:
    """
    ファイルのSHA256ハッシュを生成（重複検出用）
    """
    return hashlib.sha256(content).hexdigest()

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """
    Dropboxフォルダ内の重複ファイルを検出してログに出力。
    同一ファイルがあれば、後のものを削除する処理も含められる。
    """
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            try:
                dbx.files_delete_v2(path)
                print(f"🗑️ 削除済み: {path}")
            except Exception as e:
                print(f"❌ 削除エラー: {e}")
        else:
            hash_map[hash_value] = path