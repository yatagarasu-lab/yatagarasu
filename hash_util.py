# hash_util.py
import hashlib
import os

HASH_STORE_FILE = "processed_hashes.txt"

def file_hash(content):
    """ファイル内容のSHA256ハッシュを計算"""
    return hashlib.sha256(content).hexdigest()

def is_duplicate(content):
    """すでに処理済みのファイルか確認"""
    hash_val = file_hash(content)
    if not os.path.exists(HASH_STORE_FILE):
        return False
    with open(HASH_STORE_FILE, "r") as f:
        return hash_val in f.read().splitlines()

def save_hash(content):
    """処理済みのファイルのハッシュを保存"""
    hash_val = file_hash(content)
    with open(HASH_STORE_FILE, "a") as f:
        f.write(hash_val + "\n")
