import dropbox
import hashlib
from dotenv import load_dotenv
import os

load_dotenv()

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def save_to_dropbox(file_data, path):
    # 重複チェック用：全ファイル走査
    existing_files = dbx.files_list_folder(os.path.dirname(path)).entries
    hashes = {}

    for file in existing_files:
        try:
            _, res = dbx.files_download(file.path_display)
            content = res.content
            hash_value = file_hash(content)

            if hash_value in hashes:
                # 重複ファイルは削除
                print(f"重複ファイル削除: {file.path_display}")
                dbx.files_delete_v2(file.path_display)
            else:
                hashes[hash_value] = file.path_display
        except Exception as e:
            print(f"重複チェック失敗: {e}")

    # 新規ファイルアップロード
    try:
        dbx.files_upload(file_data, path, mode=dropbox.files.WriteMode.overwrite)
        print(f"アップロード成功: {path}")
    except Exception as e:
        print(f"アップロード失敗: {e}")