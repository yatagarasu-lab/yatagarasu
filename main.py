from flask import Flask, request
import hashlib
import dropbox
import os

app = Flask(__name__)

# 環境変数からトークンを取得
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")

# Dropbox クライアント初期化
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# ファイルのハッシュを計算
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# 指定フォルダのファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

# ファイルをダウンロード
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# 重複ファイルを削除
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            dbx.files_delete_v2(path)  # 重複ファイルを削除
        else:
            hash_map[hash_value] = path

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox webhook のチャレンジ応答
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        # ファイル処理を非同期で行う場合など、ここで通知受信
        print("Webhook POST 受信 - Dropboxファイル確認開始")
        try:
            find_duplicates()
        except Exception as e:
            print(f"エラー: {e}")
        return "Webhook received", 200

    return "Method Not Allowed", 405

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)