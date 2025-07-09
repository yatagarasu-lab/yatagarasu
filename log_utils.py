import os
import glob
from datetime import datetime, timedelta

LOG_DIR = "logs"
LOG_PATTERN = os.path.join(LOG_DIR, "*.log")


def delete_old_logs(keep_days=7):
    """指定日数より古いログファイルを削除"""
    now = datetime.now()
    for log_file in glob.glob(LOG_PATTERN):
        modified_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        if now - modified_time > timedelta(days=keep_days):
            os.remove(log_file)


def list_log_files():
    """ログファイル一覧を取得（ファイル名と更新日時）"""
    logs = []
    for log_file in glob.glob(LOG_PATTERN):
        modified_time = os.path.getmtime(log_file)
        logs.append({
            "filename": os.path.basename(log_file),
            "modified": datetime.fromtimestamp(modified_time).isoformat()
        })
    return logs


def download_log_file(filename):
    """特定のログファイルのパスを返す"""
    file_path = os.path.join(LOG_DIR, filename)
    if os.path.exists(file_path):
        return file_path
    else:
        return None