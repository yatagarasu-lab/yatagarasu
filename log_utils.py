import os
import glob
from datetime import datetime, timedelta

LOG_DIR = "logs"
LOG_PATTERN = os.path.join(LOG_DIR, "*.log")

def delete_old_logs(keep_days=7):
    now = datetime.now()
    for log_file in glob.glob(LOG_PATTERN):
        modified_time = datetime.fromtimestamp(os.path.getmtime(log_file))
        if now - modified_time > timedelta(days=keep_days):
            os.remove(log_file)
            print(f"削除しました: {log_file}")