import dropbox
import os
import hashlib

# Dropboxクライアントの初期化
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def download_file(path):
    """指定されたDropboxパスのファイルをダウンロードしてバイナリで返す"""
    try:
        metadata, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        raise Exception(f"Dropboxからのファイル取得に失敗しました: {e}")

def list_files(folder_path="/Apps/slot-data-analyzer"):
    """指定フォルダ内のファイル一覧を取得"""
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        raise Exception(f"Dropboxフォルダ一覧取得失敗: {e}")

def file_hash(content):
    """ファイルのSHA256ハッシュを算出"""
    return hashlib.sha256(content).hexdigest()

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """Dropboxフォルダ内の重複ファイルを検出し削除（任意で有効化）"""
    try:
        files = list_files(folder_path)
        hash_map = {}

        for file in files:
            path = file.path_display
            content = download_file(path)
            hash_value = file_hash(content)

            if hash_value in hash_map:
                print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
                # dbx.files_delete_v2(path)  # 実際に削除する場合はコメントを外す
            else:
                hash_map[hash_value] = path

    except Exception as e:
        print(f"重複検出エラー: {e}")