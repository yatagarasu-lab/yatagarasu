import hashlib
from services.dropbox_handler import list_files, download_file, delete_file

# ファイルのSHA-256ハッシュを計算
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# Dropboxフォルダ内で重複ファイルを検出し、削除（任意でON/OFF）
def find_duplicates(folder_path="/"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # 重複ファイルを削除する場合はこちらを有効化
            try:
                delete_file(path)
                print(f"🗑️ 削除完了: {path}")
            except Exception as e:
                print(f"❌ 削除失敗: {path} - {e}")
        else:
            hash_map[hash_value] = path
