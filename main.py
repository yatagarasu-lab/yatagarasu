# dropbox_handler.py

import os
import hashlib
import dropbox

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")  # Render の環境変数に設定
WATCH_FOLDER = "/slot-data-analyzer"  # Dropboxの監視フォルダ

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def list_dropbox_files():
    """Dropboxフォルダ内の全ファイルを取得"""
    try:
        result = dbx.files_list_folder(WATCH_FOLDER)
        files = result.entries
        while result.has_more:
            result = dbx.files_list_folder_continue(result.cursor)
            files.extend(result.entries)
        return [f for f in files if isinstance(f, dropbox.files.FileMetadata)]
    except Exception as e:
        print(f"[ERROR] Dropboxフォルダ取得エラー: {e}")
        return []

def get_file_content_and_hash(file_path):
    """Dropboxファイルの内容を取得し、ハッシュを計算"""
    _, res = dbx.files_download(file_path)
    content = res.content
    file_hash = hashlib.md5(content).hexdigest()
    return content.decode("utf-8", errors="ignore"), file_hash

def detect_new_files(existing_hashes):
    """新規ファイルのみ抽出し返す"""
    new_files = []
    for f in list_dropbox_files():
        try:
            content, file_hash = get_file_content_and_hash(f.path_lower)
            if file_hash not in existing_hashes:
                existing_hashes.add(file_hash)
                new_files.append({"name": f.name, "content": content})
        except Exception as e:
            print(f"[ERROR] ファイル解析失敗: {e}")
    return new_files, existing_hashes