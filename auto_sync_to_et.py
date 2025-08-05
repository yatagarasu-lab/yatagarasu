import os
import hashlib
import requests

# === 設定 ===
ET_CODE_ENDPOINT = os.environ.get("ET_CODE_ENDPOINT", "https://your-etcode-url.onrender.com/receive-code")
WATCH_DIR = "scripts"  # 自動送信対象フォルダ
HASH_LOG = ".sent_hashes.txt"  # ハッシュ記録ファイル

# === ユーティリティ ===
def hash_content(content):
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def load_sent_hashes():
    if not os.path.exists(HASH_LOG):
        return {}
    with open(HASH_LOG, "r", encoding="utf-8") as f:
        return dict(line.strip().split(" ") for line in f if " " in line)

def save_sent_hashes(hash_map):
    with open(HASH_LOG, "w", encoding="utf-8") as f:
        for filename, hash_value in hash_map.items():
            f.write(f"{filename} {hash_value}\n")

def send_file(filename, code):
    payload = {"filename": filename, "code": code}
    response = requests.post(ET_CODE_ENDPOINT, json=payload)
    return response.status_code, response.text

# === メイン処理 ===
def auto_sync():
    sent_hashes = load_sent_hashes()
    new_hashes = {}

    for root, _, files in os.walk(WATCH_DIR):
        for name in files:
            if not name.endswith(".py"):
                continue

            path = os.path.join(root, name)
            rel_path = os.path.relpath(path, WATCH_DIR)

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            content_hash = hash_content(content)
            new_hashes[rel_path] = content_hash

            # 前回と同じならスキップ
            if sent_hashes.get(rel_path) == content_hash:
                continue

            status, res_text = send_file(rel_path, content)
            print(f"[送信] {rel_path} → ステータス: {status} / 内容: {res_text}")

    save_sent_hashes(new_hashes)

if __name__ == "__main__":
    auto_sync()
