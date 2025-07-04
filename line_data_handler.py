import os
import zipfile
import tempfile

from dropbox_handler import upload_file

def save_line_content_to_temp_file(content: bytes, filename: str) -> str:
    """一時フォルダにファイル保存し、パスを返す"""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, filename)
    with open(temp_path, "wb") as f:
        f.write(content)
    return temp_path

def zip_and_upload(file_paths: list, zip_name="latest_upload.zip", dropbox_path="/Apps/slot-data-analyzer/latest_upload.zip"):
    """複数ファイルをZIP化してDropboxにアップロード"""
    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = os.path.join(temp_dir, zip_name)
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in file_paths:
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)

        with open(zip_path, "rb") as f:
            zip_data = f.read()
            upload_file(zip_data, dropbox_path)

        print(f"✅ ZIPアップロード成功: {dropbox_path}")
