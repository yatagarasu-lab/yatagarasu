import hashlib
import os

# ハッシュを保存するファイル
HASH_STORE_FILE = "processed_hashes.txt"

def file_hash(content):
    """ファイル内容のSHA256ハッシュを計算"""
    return hashlib.sha256(content).hexdigest()

def is_duplicate(content):
    """ファイルが既に処理済みかどうかをチェック"""
    hash_val = file_hash(content)

    if not os.path.exists(HASH_STORE_FILE):
        return False

    with open(HASH_STORE_FILE, "r") as f:
        hashes = f.read().splitlines()

    return hash_val in hashes

def save_hash(content):
    """新しいファイルのハッシュを保存"""
    hash_val = file_hash(content)

    with open(HASH_STORE_FILE, "a") as f:
        f.write(hash_val + "\n")