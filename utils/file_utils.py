# utils/file_utils.py

import os
import mimetypes

def is_text_file(filename):
    mimetype, _ = mimetypes.guess_type(filename)
    return mimetype and mimetype.startswith('text')

def is_image_file(filename):
    mimetype, _ = mimetypes.guess_type(filename)
    return mimetype and mimetype.startswith('image')

def extract_text_from_txt(content_bytes):
    try:
        return content_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return content_bytes.decode('shift_jis', errors='ignore')  # fallback

def save_temp_file(file_name, content):
    temp_path = f"/tmp/{file_name}"
    with open(temp_path, 'wb') as f:
        f.write(content)
    return temp_path