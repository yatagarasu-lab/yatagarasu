from dropbox_utils import list_files, download_file
from gpt_handler import analyze_file_and_notify
import time

def analyze_dropbox_updates():
    print("🔁 Dropbox更新を確認中...")
    files = list_files("/Apps/slot-data-analyzer")

    for file in files:
        path = file.path_display
        content = download_file(path)
        if content:
            print(f"📁 処理中: {path}")
            analyze_file_and_notify(path, content)
            time.sleep(1)