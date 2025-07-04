# dropbox_handler.py
import os
import zipfile
import tempfile
from dropbox_utils import list_files, download_file, upload_file, find_duplicates_and_delete
from gpt_utils import analyze_file_content
from line_utils import send_line_message

FOLDER_PATH = "/Apps/slot-data-analyzer"
PROCESSED_FOLDER = "/Apps/slot-data-analyzer/processed"

def process_new_files():
    print("🔍 Dropboxフォルダをスキャン中...")
    files = list_files(FOLDER_PATH)

    for file in files:
        file_path = file.path_display

        # processedフォルダはスキップ
        if file_path.startswith(PROCESSED_FOLDER):
            continue

        print(f"📂 ファイル発見: {file_path}")
        content = download_file(file_path)

        print(f"🧠 GPTで解析中: {file_path}")
        analysis_result = analyze_file_content(content)

        print(f"📤 LINE通知送信中: {file_path}")
        send_line_message(f"📁 新規ファイル: {file_path}\n\n📝 解析結果:\n{analysis_result}")

        # ZIP圧縮 → 処理済みに保存
        zip_name = os.path.splitext(os.path.basename(file_path))[0] + ".zip"
        zip_path = f"{PROCESSED_FOLDER}/{zip_name}"
        upload_compressed_file(content, zip_path)

        # 元ファイルを削除（Dropbox内）
        from dropbox_auth import get_dropbox_access_token
        import dropbox
        dbx = dropbox.Dropbox(oauth2_access_token=get_dropbox_access_token())
        dbx.files_delete_v2(file_path)
        print(f"🗑️ 元ファイル削除: {file_path}")

    # 重複ファイルの検出と削除
    print("🔁 重複ファイルチェック中...")
    find_duplicates_and_delete(FOLDER_PATH)

def upload_compressed_file(content, dropbox_path):
    from dropbox import Dropbox
    from dropbox_auth import get_dropbox_access_token

    dbx = Dropbox(oauth2_access_token=get_dropbox_access_token())

    # 一時ファイルにZIP保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp_zip:
        with zipfile.ZipFile(tmp_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr("data", content)
        tmp_zip.flush()
        with open(tmp_zip.name, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
        os.unlink(tmp_zip.name)