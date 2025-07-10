import os
import hashlib
import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from utils import get_file_type, download_file, file_hash, ocr_image
from gpt_handler import analyze_content
from line_handler import push_line_message

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# リフレッシュトークンを使って認証
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

# Dropboxフォルダ内のファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    try:
        result = dbx.files_list_folder(folder_path)
        return result.entries
    except Exception as e:
        print(f"Dropbox一覧取得エラー: {e}")
        return []

# ファイルごとに処理
def handle_dropbox_update():
    files = list_files()
    hash_map = {}
    for file in files:
        path = file.path_display
        content = download_file(path)
        if content is None:
            continue

        # 重複チェック
        hash_val = file_hash(content)
        if hash_val in hash_map:
            print(f"[重複検出] {path}（同一: {hash_map[hash_val]}）")
            # dbx.files_delete_v2(path)  # 必要なら削除
            continue
        hash_map[hash_val] = path

        # ファイル種別判定と解析
        extension = get_file_type(file.name)
        if extension in ["jpg", "jpeg", "png"]:
            extracted_text = ocr_image(content)
            result = analyze_content(file.name, extracted_text)
        elif extension in ["txt", "log", "csv"]:
            result = analyze_content(file.name, content.decode("utf-8"))
        else:
            result = f"[未対応] 拡張子: {extension}"

        print(f"✅ {file.name} の解析結果:\n{result}\n")
        push_line_message(result)