import os
import zipfile
import io
from dropbox_handler import list_files, download_file, upload_file, delete_file

def compress_files_in_dropbox(folder_path="/Apps/slot-data-analyzer", zip_name="latest_upload.zip"):
    """Dropbox内のファイルをまとめてZIP化し、1ファイルとして保存する"""
    files = list_files(folder_path)
    if not files:
        return "❌ 圧縮対象ファイルが見つかりませんでした。"

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            path = file.path_display
            if path.endswith(".zip"):
                continue  # 既にZIPのものは除外
            content = download_file(path)
            filename = os.path.basename(path)
            zipf.writestr(filename, content)

    zip_buffer.seek(0)
    zip_path = f"{folder_path}/{zip_name}"

    # 圧縮ファイルをアップロード（既存あれば上書き）
    upload_file(zip_path, zip_buffer.read())

    # 元ファイルを削除してスッキリさせる（必要あれば）
    for file in files:
        if not file.path_display.endswith(".zip"):
            delete_file(file.path_display)

    return f"✅ Dropbox内の{len(files)}ファイルを圧縮 → {zip_name}として保存しました。"
