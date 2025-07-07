import os
from dropbox_utils import list_files, download_file, file_hash

# ファイル一覧から重複ファイルを検出して削除（内容が同一なら削除）
def clean_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_val = file_hash(content)

        if hash_val in hash_map:
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_val]}）")
            # 不要なファイルは削除する（本番時有効化）
            # dbx.files_delete_v2(path)
        else:
            hash_map[hash_val] = path

# ファイルの内容を表示・確認用（分析処理の前に読み取るなど）
def get_file_contents(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    contents = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        contents[path] = content

    return contents