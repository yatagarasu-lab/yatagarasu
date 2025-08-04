from dropbox_auth import get_dropbox_client

def list_files(folder_path="/Apps/slot-data-analyzer"):
    dbx = get_dropbox_client()
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    dbx = get_dropbox_client()
    _, res = dbx.files_download(path)
    return res.content

def delete_file(path):
    dbx = get_dropbox_client()
    dbx.files_delete_v2(path)

def upload_file(path, content):
    dbx = get_dropbox_client()
    dbx.files_upload(content, path, mode=dropbox.files.WriteMode("overwrite"))