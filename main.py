# main.py

import os
import hashlib
import dropbox
from flask import Flask, request

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
WATCH_FOLDER = "/Apps/slot-data-analyzer"  # Dropboxでの実際の保存場所に合わせて変更
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# 保存済みファイルのハッシュ一覧
existing_hashes = {}

# Dropbox内のファイル一覧取得
def list_dropbox_files():
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

# ファイル内容取得とハッシュ計算
def get_file_content_and_hash(file_path):
    _, res = dbx.files_download(file_path)
    content = res.content
    file_hash = hashlib.md5(content).hexdigest()
    return content.decode("utf-8", errors="ignore"), file_hash

# 新規ファイルの検出
def detect_new_files(existing_hashes):
    new_files = []
    files = list_dropbox_files()
    for f in files:
        try:
            content, file_hash = get_file_content_and_hash(f.path_lower)
            if file_hash not in existing_hashes:
                existing_hashes[file_hash] = f.name
                new_files.append({
                    "name": f.name,
                    "path": f.path_display,
                    "content": content
                })
        except Exception as e:
            print(f"[ERROR] ファイル処理エラー: {e}")
    return new_files

# Flaskアプリ（Webhook受信用）
app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    new_files = detect_new_files(existing_hashes)
    if new_files:
        print(f"[INFO] 新しいファイルを検出: {len(new_files)} 件")
        for f in new_files:
            print(f"\n📄 {f['name']} の内容:\n{f['content'][:500]}...\n")  # 内容の先頭だけ表示
    else:
        print("[INFO] 新しいファイルはありません")
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)