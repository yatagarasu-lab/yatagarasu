# utils/file_type.py

import mimetypes
import os

def is_image_file(file_path):
    """
    拡張子またはMIMEタイプから画像ファイルかどうかを判定
    :param file_path: Dropbox上のファイルパス
    :return: True（画像）/ False（画像でない）
    """
    mimetype, _ = mimetypes.guess_type(file_path)
    if mimetype and mimetype.startswith("image/"):
        return True

    # ファイル名から拡張子で判定する場合（念のため）
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"]
    _, ext = os.path.splitext(file_path.lower())
    return ext in image_extensions
