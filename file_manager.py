import os
import hashlib
from services.dropbox_handler import list_files, move_file, download_file, create_folder_if_not_exists

# フォルダ名定義
PROCESSED_FOLDER = "/processed"
DUPLICATE_FOLDER = "/duplicates"

# ハッシュ生成関数（重複検出用）
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# Dropbox内のファイルを整理するメイン関数
def organize_dropbox_files():
    print("[整理開始] Dropboxファイルの重複確認とフォルダ移動を実行します...")
    files = list_files("/")
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            # 重複ファイル → duplicatesフォルダへ
            print(f"[重複検出] {path} は {hash_map[hash_value]} と同一内容")
            create_folder_if_not_exists(DUPLICATE_FOLDER)
            move_file(path, DUPLICATE_FOLDER + "/" + os.path.basename(path))
        else:
            # 新規ファイル → processedフォルダへ
            create_folder_if_not_exists(PROCESSED_FOLDER)
            move_file(path, PROCESSED_FOLDER + "/" + os.path.basename(path))
            hash_map[hash_value] = path

    print("[整理完了]")
