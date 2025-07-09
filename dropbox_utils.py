import dropbox
import os
from datetime import datetime

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def move_file_to_month_folder(path):
    """
    指定ファイルを /Apps/slot-data-analyzer/YYYY-MM/ に移動
    """
    now = datetime.now()
    month_folder = f"/Apps/slot-data-analyzer/{now.strftime('%Y-%m')}"
    filename = path.split("/")[-1]
    new_path = f"{month_folder}/{filename}"

    # フォルダがない場合は作成（存在済みなら無視）
    try:
        dbx.files_create_folder_v2(month_folder)
    except dropbox.exceptions.ApiError as e:
        if not (isinstance(e.error, dropbox.files.CreateFolderError) and e.error.get_path().is_conflict()):
            raise

    # ファイルを移動
    dbx.files_move_v2(from_path=path, to_path=new_path, allow_shared_folder=True, autorename=True)
    return new_path