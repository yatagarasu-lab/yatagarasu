import time
from services.dropbox_handler import get_latest_dropbox_file_path
from yatagarasu import analyze_file
from line_notify import send_line_message

# 前回通知済みのファイルパスを保持（メモリ上）
last_notified_file = None

def monitor_dropbox_and_notify(interval=300):
    global last_notified_file
    print(f"[監視開始] Dropboxを{interval}秒ごとにチェックします...")

    while True:
        try:
            path = get_latest_dropbox_file_path()
            if path and path != last_notified_file:
                print(f"[新ファイル検出] {path}")
                result = analyze_file(path)
                send_line_message(f"📝新規解析ファイル:\n{path}\n\n📊解析結果:\n{result}")
                last_notified_file = path
            else:
                print("[変化なし] 新しいファイルは見つかりませんでした。")

        except Exception as e:
            print(f"[エラー] {e}")
        
        time.sleep(interval)