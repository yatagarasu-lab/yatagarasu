# processor.py

import dropbox
import os
from hash_util import file_hash
from notifier import notify
from ocr_utils import extract_text_from_image
from predictor import analyze_text
from log_utils import log

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_files(folder_path=DROPBOX_FOLDER_PATH):
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        log(f"❌ Dropboxフォルダ読み込みエラー: {e}")
        return []

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def process_file(file_entry):
    file_path = file_entry.path_display
    try:
        # ファイルダウンロードと重複チェック
        content = download_file(file_path)
        content_hash = file_hash(content)

        # ログ保存先に同じhashがないか確認（簡易的にファイル名でチェック）
        hash_path = f"{DROPBOX_FOLDER_PATH}/.hashes/{content_hash}.txt"
        try:
            dbx.files_get_metadata(hash_path)
            log(f"⚠️ 重複ファイル: {file_path}")
            return
        except dropbox.exceptions.ApiError:
            pass  # 存在しないのでOK

        # OCR処理・要約処理
        extracted_text = extract_text_from_image(content)
        summary = analyze_text(extracted_text)

        # LINE通知
        notify(f"🧠 新規ファイル解析結果:\n{summary}", line=True)

        # ハッシュ記録ファイルとして保存
        dbx.files_upload(b"processed", hash_path, mode=dropbox.files.WriteMode.overwrite)
        log(f"✅ 処理完了: {file_path}")

    except Exception as e:
        log(f"❌ ファイル処理エラー（{file_path}）: {e}")

def process_all_files():
    files = list_files(DROPBOX_FOLDER_PATH)
    for file_entry in files:
        if isinstance(file_entry, dropbox.files.FileMetadata):
            process_file(file_entry)