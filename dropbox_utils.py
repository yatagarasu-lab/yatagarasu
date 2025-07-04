import zipfile
import io
from dropbox_handler import list_files, download_file, file_hash, delete_file, upload_bytes

def find_and_remove_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """Dropbox内の重複ファイルを検出して削除"""
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            delete_file(path)
        else:
            hash_map[hash_value] = path

def compress_all_files(folder_path="/Apps/slot-data-analyzer", output_zip_name="/Apps/slot-data-analyzer/圧縮アーカイブ.zip"):
    """Dropbox内の全ファイルを1つのzipにまとめて保存"""
    files = list_files(folder_path)
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            path = file.path_display
            content = download_file(path)
            filename = path.split("/")[-1]
            zipf.writestr(filename, content)

    upload_bytes(zip_buffer.getvalue(), output_zip_name)