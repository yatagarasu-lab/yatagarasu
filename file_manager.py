import dropbox
from dropbox.files import FileMetadata
from auth_dropbox import get_dropbox_access_token

def get_dropbox_client():
    access_token = get_dropbox_access_token()
    return dropbox.Dropbox(access_token)

def list_files(folder_path="/"):
    dbx = get_dropbox_client()
    result = dbx.files_list_folder(folder_path)
    files = [entry for entry in result.entries if isinstance(entry, FileMetadata)]
    return files

def organize_dropbox_files(folder_path="/"):
    files = list_files(folder_path)
    if not files:
        return None
    latest = sorted(files, key=lambda f: f.server_modified, reverse=True)[0]
    return latest