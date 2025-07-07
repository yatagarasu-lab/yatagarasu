import hashlib
import dropbox
import os
from dropbox_utils import list_files, download_file

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# ハッシュ関数（SHA256）で内容を一意に判定
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# 重複ファイルを検出し、削除する（オプション）
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    duplicates = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            duplicates.append((path, hash_map[hash_value]))
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            try:
                dbx.files_delete_v2(path)
                print(f"🗑️ 削除しました: {path}")
            except Exception as e:
                print(f"❌ 削除失敗: {path} → {e}")
        else:
            hash_map[hash_value] = path

    return duplicates

# 全ファイルの内容を結合して1つのテキストに
def combine_all_files(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    combined_text = ""

    for file in files:
        path = file.path_display
        content = download_file(path)
        try:
            content = content.decode("utf-8", errors="ignore")
            combined_text += f"\n\n===== {os.path.basename(path)} =====\n{content}"
        except Exception as e:
            combined_text += f"\n\n===== {os.path.basename(path)} =====\n⚠️ テキストとして読み込めませんでした: {e}"

    return combined_text
