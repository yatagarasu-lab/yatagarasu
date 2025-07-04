# dropbox_utils.py
import os
import dropbox
import hashlib
from dotenv import load_dotenv
from gpt_utils import analyze_file_content
from line_utils import push_message_to_line

load_dotenv()
DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
WATCH_FOLDER = os.getenv("DROPBOX_WATCH_FOLDER", "/Apps/slot-data-analyzer")

dbx = dropbox.Dropbox(DROPBOX_TOKEN)

def handle_dropbox_event():
    files = list_files(WATCH_FOLDER)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            dbx.files_delete_v2(path)
            print(f"重複ファイル削除: {path}")
        else:
            hash_map[hash_value] = path
            result = analyze_file_content(content)
            push_message_to_line(f"📝解析完了: {path}\n\n{result[:1000]}")

def list_files(folder_path):
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content.decode('utf-8')

def file_hash(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()
