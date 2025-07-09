import os
import dropbox
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_LOG_FOLDER = "/logs"

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)


def list_log_files(date: str = None):
    """
    指定日のログファイル一覧を取得する（指定なしなら当日）
    例: date="2025-07-06"
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    folder_path = f"{DROPBOX_LOG_FOLDER}/{date}"

    try:
        res = dbx.files_list_folder(folder_path)
        return [entry.name for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)]
    except Exception as e:
        print(f"❌ ログファイル取得エラー: {e}")
        return []


def download_log_file(filename: str, date: str = None) -> str:
    """
    指定ログファイルの中身をテキストとして取得
    """
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
    path = f"{DROPBOX_LOG_FOLDER}/{date}/{filename}"

    try:
        _, res = dbx.files_download(path)
        content = res.content.decode("utf-8")
        return content
    except Exception as e:
        print(f"❌ ログファイル読み込みエラー: {e}")
        return ""


def delete_old_logs(keep_days: int = 7):
    """
    指定日数より古いログフォルダを自動削除
    """
    try:
        res = dbx.files_list_folder(DROPBOX_LOG_FOLDER)
        folders = [entry for entry in res.entries if isinstance(entry, dropbox.files.FolderMetadata)]

        now = datetime.now()
        for folder in folders:
            folder_date_str = folder.name
            try:
                folder_date = datetime.strptime(folder_date_str, "%Y-%m-%d")
                delta = (now - folder_date).days
                if delta > keep_days:
                    dbx.files_delete_v2(f"{DROPBOX_LOG_FOLDER}/{folder_date_str}")
                    print(f"🧹 削除: {folder_date_str}")
            except ValueError:
                continue

    except Exception as e:
        print(f"❌ 古いログ削除エラー: {e}")
