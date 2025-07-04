import os
import io
import zipfile
from dropbox_handler import list_files, download_file, file_hash, delete_file
from PIL import Image

def compress_image(image_bytes, quality=60):
    """画像をJPEGに圧縮（サイズ軽減）"""
    try:
        image = Image.open(io.BytesIO(image_bytes))
        output = io.BytesIO()
        image.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        print(f"❌ 圧縮失敗: {e}")
        return image_bytes  # 圧縮できなかった場合はそのまま返す

def find_and_remove_duplicates(folder_path="/Apps/slot-data-analyzer"):
    """重複ファイルを見つけて削除"""
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        if not content:
            continue

        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"⚠️ 重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            delete_file(path)
        else:
            hash_map[hash_value] = path

def compress_all_images(folder_path="/Apps/slot-data-analyzer"):
    """フォルダ内の画像ファイルを一括圧縮"""
    files = list_files(folder_path)
    for file in files:
        path = file.path_display
        if path.lower().endswith((".jpg", ".jpeg", ".png")):
            original = download_file(path)
            if original:
                compressed = compress_image(original)
                if len(compressed) < len(original):
                    try:
                        from dropbox_handler import dbx  # 再import
                        dbx.files_upload(compressed, path, mode=dropbox.files.WriteMode.overwrite)
                        print(f"📦 圧縮済: {path}")
                    except Exception as e:
                        print(f"⚠️ 上書き失敗: {path} - {e}")