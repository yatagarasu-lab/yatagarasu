import time
import threading
from dropbox_handler import list_and_filter_files, download_file, file_hash
from dropbox_handler import upload_file, save_to_dropbox, is_image, is_text
from gpt_handler import process_file_with_gpt
from line_notify import push_message
import os

# ロックを使って排他制御
lock = threading.Lock()

def analyze_and_notify(file_path, file_type, filename):
    content = download_file(file_path)
    result = process_file_with_gpt(content, file_type)

    message = f"📢 解析完了\nファイル名: {filename}\nタイプ: {file_type}\n\n📄 要約:\n{result}"
    push_message(message)

def monitor_dropbox():
    print("🔁 Dropboxフォルダの監視を開始します...")
    checked_hashes = set()

    while True:
        try:
            with lock:
                files = list_and_filter_files()
                for file in files:
                    path = file.path_display
                    filename = os.path.basename(path)
                    content = download_file(path)
                    hash_val = file_hash(content)

                    if hash_val in checked_hashes:
                        continue  # 重複解析を防ぐ

                    checked_hashes.add(hash_val)
                                        # ファイルタイプの判定
                    if is_image(filename):
                        file_type = "image"
                    elif is_text(filename):
                        file_type = "text"
                    else:
                        print(f"❌ 対応外のファイル形式: {filename}")
                        continue

                    print(f"🧠 新しいファイルを解析中: {filename}")
                    analyze_and_notify(path, file_type, filename)

        except Exception as e:
            print(f"⚠️ エラーが発生しました: {e}")

        time.sleep(60)  # 60秒ごとに監視
                    if __name__ == "__main__":
    print("🕒 定時監視BOT 起動中（1分ごとにDropboxを監視）")
    monitor_dropbox()