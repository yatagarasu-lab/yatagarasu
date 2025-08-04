import hashlib
from dropbox_auth import get_dropbox_client

def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    dbx = get_dropbox_client()
    _, res = dbx.files_download(path)
    return res.content

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    duplicates = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        h = file_hash(content)
        if h in hash_map:
            duplicates.append((path, hash_map[h]))
        else:
            hash_map[h] = path
    
    return duplicates