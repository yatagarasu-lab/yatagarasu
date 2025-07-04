# dropbox_handler.py
import os
from dropbox_utils import list_files, download_file, upload_file, find_duplicates
from gpt_utils import analyze_file_content
from line_utils import send_line_message

FOLDER_PATH = "/Apps/slot-data-analyzer"
PROCESSED_FOLDER = "/Apps/slot-data-analyzer/processed"

def process_new_files():
    print("🔍 Dropboxフォルダをスキャン中...")
    files = list_files(FOLDER_PATH)

    for file in files:
        file_path = file.path_display

        # processed フォルダはスキップ
        if file_path.startswith(PROCESSED_FOLDER):
            continue

        print(f"📂 ファイル発見: {file_path}")
        content = download_file(file_path)

        print(f"🧠 GPTで解析中: {file_path}")
        analysis_result = analyze_file_content(content)

        print(f"📤 LINE通知送信中: {file_path}")
        send_line_message(f"📁 新規ファイル: {file_path}\n\n📝 解析結果:\n{analysis_result}")

        # 処理済みに移動
        new_path = f"{PROCESSED_FOLDER}/{os.path.basename(file_path)}"
        upload_file_path(content, new_path)

    # 重複チェック（通知のみにして削除はしない）
    print("🔁 重複ファイルチェック中...")
    find_duplicates(FOLDER_PATH)

def upload_file_path(content, dropbox_path):
    from dropbox import Dropbox
    from dropbox_auth import get_dropbox_access_token
    import tempfile

    dbx = Dropbox(oauth2_access_token=get_dropbox_access_token())

    # 一時ファイルとして保存しアップロード
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(content)
        tmp_file.flush()
        with open(tmp_file.name, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

        os.unlink(tmp_file.name)