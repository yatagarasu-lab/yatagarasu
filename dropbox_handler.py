import dropbox
import hashlib
import os

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)


def upload_file_from_bytes(dropbox_path: str, file_bytes: bytes):
    """
    バイトデータをDropboxにアップロード
    """
    try:
        dbx.files_upload(file_bytes, dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
        print(f"✅ Dropboxにアップロード成功: {dropbox_path}")
    except Exception as e:
        print(f"❌ Dropboxアップロード失敗: {e}")


def download_file(dropbox_path: str) -> bytes:
    """
    Dropbox上のファイルをダウンロードしてバイトデータで返す
    """
    try:
        metadata, res = dbx.files_download(dropbox_path)
        print(f"✅ Dropboxからダウンロード成功: {dropbox_path}")
        return res.content
    except Exception as e:
        print(f"❌ Dropboxダウンロード失敗: {e}")
        return b""


def list_files(folder_path="/Apps/slot-data-analyzer") -> list:
    """
    指定フォルダ内のファイル一覧を取得
    """
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"❌ Dropboxフォルダリスト取得失敗: {e}")
        return []


def file_hash(content: bytes) -> str:
    """
    バイトデータのSHA256ハッシュを返す（重複判定用）
    """
    return hashlib.sha256(content).hexdigest()


def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """
    Dropboxフォルダ内の重複ファイルを検出・削除（任意で削除ONに）
    """
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # dbx.files_delete_v2(path)  # 削除するならコメントを外す
        else:
            hash_map[hash_value] = path