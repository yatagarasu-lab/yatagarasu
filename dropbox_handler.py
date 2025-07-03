import dropbox
import hashlib

DROPBOX_ACCESS_TOKEN =s.a.a.a.a.a.ssssssssssssssssssssssssssssssssssd0000b0b0b0b0b0b0b0b0b0b0b0b0buuuuuuuuuuueuuetttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttttt

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    metadata, response = dbx.files_download(path)
    return response.content

def file_hash(content):
    return hashlib.md5(content).hexdigest()