from dropbox_handler import list_files, download_file, file_hash, delete_file

def find_and_remove_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """Dropbox内の重複ファイルを検出・削除する"""
    files = list_files(folder_path)
    hash_map = {}
    duplicate_count = 0

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出 → 削除: {path}（同一: {hash_map[hash_value]}）")
            delete_file(path)
            duplicate_count += 1
        else:
            hash_map[hash_value] = path

    print(f"✅ 処理完了: 重複ファイル {duplicate_count} 件削除しました")