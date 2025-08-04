import dropbox
import os
import hashlib
from services.gpt_summarizer import summarize_file
from utils.line_notify import notify_user
from utils.file_cache import FileCache

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_ROOT_PATH = ""  # フルアクセスの場合は空欄でOK
cache = FileCache()

def get_dropbox_client():
    return dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def process_dropbox_delta(account_id):
    dbx = get_dropbox_client()
    result = dbx.files_list_folder(DROPBOX_ROOT_PATH)

    for entry in result.entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            path = entry.path_display
            if cache.is_duplicate(path, entry.content_hash):
                continue

            metadata, res = dbx.files_download(path)
            content = res.content

            summary = summarize_file(content, metadata.name)

            notify_user(f"📝 {metadata.name} の要約:\n{summary}")
            cache.update(path, entry.content_hash)