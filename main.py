from flask import Flask, request
import hashlib
import dropbox
import os

app = Flask(__name__)

DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# Dropbox クライアント初期化
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            dbx.files_delete_v2(path)  # 重複削除（必要に応じて）
        else:
            hash_map[hash_value] = path

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox webhook challenge 応答
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        print("Webhook received from Dropbox.")
        # 実行したい処理をここに書く（例：解析トリガー）
        find_duplicates()
        return "Webhook received", 200

    return "Method Not Allowed", 405

if __name__ == "__main__":
    app.run(debug=True)