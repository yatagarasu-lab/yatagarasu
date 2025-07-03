import json
from dropbox_handler import list_files, download_file, file_hash
from line_notify import send_line_message

analyzed_hashes = set()

def analyze_new_files():
    files = list_files()
    for file in files:
        if not file.name.endswith(".txt"):
            continue
        content = download_file(file.path_display)
        hash_val = file_hash(content)
        if hash_val in analyzed_hashes:
            continue
        analyzed_hashes.add(hash_val)
        text = content.decode("utf-8")
        summary = summarize_text(text)
        send_line_message(f"新しい解析結果:\n{summary}")

def summarize_text(text):
    lines = text.splitlines()
    summary = "\n".join(lines[:5])
    return summary