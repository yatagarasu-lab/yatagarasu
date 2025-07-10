import os
import hashlib
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# SHA256ハッシュを取得（テキスト or バイナリ対応）
def hash_content(content):
    if isinstance(content, str):
        content = content.encode('utf-8')
    return hashlib.sha256(content).hexdigest()

# 現在時刻のタイムスタンプ（日本時間）
def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ファイル名から拡張子を取得
def get_file_extension(filename):
    return os.path.splitext(filename)[1].lower()

# 拡張子が画像ファイルか判定
def is_image_file(filename):
    return get_file_extension(filename) in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]

# 拡張子がテキストファイルか判定
def is_text_file(filename):
    return get_file_extension(filename) in [".txt", ".md", ".csv", ".json"]