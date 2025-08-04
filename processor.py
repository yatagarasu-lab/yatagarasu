# processor.py

import os
import dropbox
from dropbox.exceptions import AuthError
from utils import download_file_content, get_file_hash, send_line_message
from log_utils import log

# Dropbox接続設定（環境変数）
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"

# ハッシュ記録（簡易的に同一セッション内で重複防止）
file_hash_map = {}

def process_all_files():
    if not DROPBOX_ACCESS_TOKEN:
        log("❌ Dropboxアクセストークン未設定")
        return

    try:
        dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
        entries = dbx.files_list_folder(DROPBOX_FOLDER_PATH).entries
    except AuthError as e:
        log(f"❌ Dropbox認証エラー: {e}")
        return

    for entry in entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            file_path = entry.path_display
            try:
                content = download_file_content(dbx, file_path)
                hash_val = get_file_hash(content)
                if hash_val in file_hash_map:
                    log(f"⚠️ 重複ファイル検出（スキップ）: {file_path}")
                    continue

                file_hash_map[hash_val] = file_path

                # ✅ GPTで解析（ここではダミー処理）
                result = f"🔍 GPT解析結果: ファイル「{file_path}」の内容を確認しました。"

                # ✅ LINEに通知（または他の処理）
                send_line_message(result)
                log(f"✅ ファイル解析成功: {file_path}")

            except Exception as e:
                log(f"❌ ファイル処理中にエラー: {file_path} → {e}")