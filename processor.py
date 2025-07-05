# processor.py
import os
import time
from dropbox_handler import list_files, download_file, delete_file
from gpt_handler import analyze_file_with_gpt, is_slot_related
from line_handler import send_line_message
import hashlib

PROCESSED_HASHES_FILE = "processed_hashes.txt"
USER_ID = os.getenv("LINE_USER_ID")

# ファイルのハッシュ値を計算
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# 処理済みハッシュを読み込む
def load_processed_hashes():
    if not os.path.exists(PROCESSED_HASHES_FILE):
        return set()
    with open(PROCESSED_HASHES_FILE, "r") as f:
        return set(line.strip() for line in f.readlines())

# 処理済みハッシュを保存
def save_processed_hash(hash_value):
    with open(PROCESSED_HASHES_FILE, "a") as f:
        f.write(f"{hash_value}\n")

# Dropboxフォルダのファイルを処理
def process_files():
    print("[INFO] 処理開始...")
    processed_hashes = load_processed_hashes()
    files = list_files()

    for file in files:
        path = file.path_display
        content = download_file(path)
        if not content:
            continue

        hash_value = file_hash(content)
        if hash_value in processed_hashes:
            print(f"[SKIP] 重複ファイル: {path}")
            continue

        # テキスト形式に変換（画像ならOCRなどは未対応）
        text = content.decode("utf-8", errors="ignore")

        # GPTで内容を分析
        result = analyze_file_with_gpt(path, text)

        if "無関係" in result or not is_slot_related(result):
            print(f"[DELETE] 非スロット: {path}")
            delete_file(path)
            continue

        # スロット関連なので通知
        send_line_message(USER_ID, f"📊 スロットデータ検出:\n\n{result}")
        print(f"[OK] 通知送信: {path}")

        save_processed_hash(hash_value)

    print("[INFO] 処理完了。")
