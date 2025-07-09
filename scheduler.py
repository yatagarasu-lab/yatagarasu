import threading
import time
from datetime import datetime
from pytz import timezone
from analyze_file import analyze_dropbox_files

def is_nighttime():
    jst = timezone("Asia/Tokyo")
    now = datetime.now(jst)
    return now.hour >= 22 or now.hour < 6

def analyze_if_night():
    if is_nighttime():
        print("[🔍] 夜間時間帯。Dropbox解析を実行中...")
        analyze_dropbox_files()
    else:
        print("[🌞] 日中時間帯のため解析をスキップ中...")

def start_scheduled_tasks():
    def loop():
        while True:
            analyze_if_night()
            time.sleep(15 * 60)  # 15分ごとにチェック

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()