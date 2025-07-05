def file_hash(content):
    return md5(content).hexdigest()

def delete_file(path):
    try:
        dbx.files_delete_v2(path)
        print(f"[delete_file] Deleted: {path}")
    except Exception as e:
        print(f"[delete_file] Error: {e}")

def find_duplicates(folder_path=DROPBOX_FOLDER_PATH):
    files = list_files(folder_path)
    hash_map = {}
    for file in files:
        path = file.path_display
        content = download_file(path)
        if content is None:
            continue
        hash_value = file_hash(content)
        if hash_value in hash_map:
            print(f"[find_duplicates] Duplicate found: {path} (same as {hash_map[hash_value]})")
            delete_file(path)
        else:
            hash_map[hash_value] = path