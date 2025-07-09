import dropbox
import os
from datetime import datetime

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def move_file_to_month_folder(original_path):
    """
    ファイルをDropbox内の月別フォルダへ移動
    """
    try:
        now = datetime.now()
        month_folder = now.strftime("/Apps/slot-data-analyzer/%Y-%m")
        file_name = os.path.basename(original_path)
        new_path = f"{month_folder}/{file_name}"

        dbx.files_move_v2(original_path, new_path)
        return new_path
    except Exception as e:
        return f"[Dropbox移動エラー] {e}"