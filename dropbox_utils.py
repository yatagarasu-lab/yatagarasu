from dropbox_handler import list_files, download_file, file_hash, delete_file

def find_and_remove_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """重複ファイルを検出し、Dropboxから削除する"""
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            delete_file(path)
        else:
            hash_map[hash_value] = path