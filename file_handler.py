from dropbox_utils import list_files, download_file
from gpt_utils import summarize_text
from line_notify import send_line_message
import hashlib

PROCESSED_HASHES = set()

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def handle_dropbox_file():
    files = list_files()
    new_messages = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in PROCESSED_HASHES:
            continue

        PROCESSED_HASHES.add(hash_value)

        try:
            text = content.decode("utf-8", errors="ignore")
            summary = summarize_text(text)
            new_messages.append(f"📝 {file.name}\n{summary}")
        except Exception as e:
            new_messages.append(f"📷 {file.name}（画像または解析不可）")

    if new_messages:
        send_line_message("\n\n".join(new_messages))
    else:
        print("🟰 No new files to process.")
