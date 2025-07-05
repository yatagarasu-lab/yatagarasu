import dropbox
import hashlib
import os

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def download_file(path: str) -> bytes:
    """
    Dropboxの指定パスからファイルをダウンロード
    """
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"❌ Dropboxファイルのダウンロード失敗: {e}")
        raise

def list_files(folder_path: str = "/Apps/slot-data-analyzer") -> list:
    """
    指定フォルダ内のファイル一覧を取得
    """
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"❌ Dropboxフォルダの一覧取得失敗: {e}")
        return []

def file_hash(content: bytes) -> str:
    """
    コンテンツのSHA256ハッシュを生成（重複チェック用）
    """
    return hashlib.sha256(content).hexdigest()

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """
    Dropbox内で同一内容の重複ファイルを検出・（必要なら）削除
    """
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        try:
            content = download_file(path)
            hash_value = file_hash(content)

            if hash_value in hash_map:
                print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
                # dbx.files_delete_v2(path)  # ←必要なら削除を有効に
            else:
                hash_map[hash_value] = path

        except Exception as e:
            print(f"❌ 重複チェック失敗: {e}")