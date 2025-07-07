import os
import dropbox
import hashlib

# 環境変数から各種情報を取得
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"

# Dropbox にリフレッシュトークンで接続
def get_dropbox_client():
    from dropbox.oauth import DropboxOAuth2FlowNoRedirect
    from dropbox.oauth import DropboxOAuth2Flow
    from dropbox.oauth import OAuth2AccessToken

    oauth_result = dropbox.DropboxOAuth2FlowNoRedirect(
        consumer_key=DROPBOX_APP_KEY,
        consumer_secret=DROPBOX_APP_SECRET,
        token_access_type="offline"
    )
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )
    return dbx

dbx = get_dropbox_client()

# 指定フォルダ内のファイル一覧を取得
def list_files(folder_path=DROPBOX_FOLDER_PATH):
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"list_files エラー: {e}")
        return []

# ファイルをダウンロードして内容を返す
def download_file(path):
    try:
        _, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"download_file エラー: {e}")
        return None

# ファイルのハッシュ値を生成
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# 重複ファイルを検出し、必要なら削除
def find_duplicates(folder_path=DROPBOX_FOLDER_PATH):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        if content is None:
            continue
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            # dbx.files_delete_v2(path)  # ←削除を有効にする場合はコメント解除
        else:
            hash_map[hash_value] = path