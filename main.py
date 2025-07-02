# 再度表示する（セッションリセットされたため）
import ace_tools as tools
import pandas as pd

requirements_txt = """
flask
dropbox
python-dotenv
"""

utils_py = """
import hashlib
import dropbox
import os
import requests

# 重複判定: 同じハッシュ値のファイルかどうか
def is_duplicate(content):
    hash_value = hashlib.md5(content).hexdigest()
    if not os.path.exists("hashes.txt"):
        with open("hashes.txt", "w") as f:
            f.write(hash_value + "\\n")
        return False

    with open("hashes.txt", "r+") as f:
        hashes = f.read().splitlines()
        if hash_value in hashes:
            return True
        f.write(hash_value + "\\n")
        return False

# 任意のファイル解析ロジック（仮のサンプル）
def analyze_file(content):
    text = content.decode("utf-8", errors="ignore")
    lines = text.split("\\n")
    word_count = sum(len(line.split()) for line in lines)
    return f"ファイルの行数: {len(lines)} 行、単語数: {word_count} 語"

# LINE通知関数
def notify_line(message):
    token = os.getenv("LINE_NOTIFY_TOKEN")
    if not token:
        print("LINEトークンが設定されていません")
        return
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {
        "message": message
    }
    requests.post("https://notify-api.line.me/api/notify", headers=headers, data=data)
"""

env_template = """
DROPBOX_TOKEN=あなたのDropboxアクセストークン
LINE_NOTIFY_TOKEN=あなたのLINE Notifyトークン
"""

main_py = """
from flask import Flask, request, jsonify
import dropbox
import os
from utils import is_duplicate, analyze_file, notify_line

app = Flask(__name__)

DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN")
DROPBOX_FOLDER = "/スロットデータ"
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        entries = dbx.files_list_folder(DROPBOX_FOLDER).entries
        for entry in entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                _, ext = os.path.splitext(entry.name)
                if ext.lower() in [".txt"]:
                    _, res = dbx.files_download(entry.path_display)
                    content = res.content

                    if is_duplicate(content):
                        dbx.files_delete_v2(entry.path_display)
                    else:
                        result = analyze_file(content)
                        notify_line(f"新規ファイル解析結果: {result}")
        return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
"""

files = {
    "main.py": main_py,
    "utils.py": utils_py,
    ".env": env_template,
    "requirements.txt": requirements_txt,
}
tools.display_dataframe_to_user(name="Dropbox解析BOT完全コード一覧", dataframe=pd.DataFrame(files.items(), columns=["ファイル名", "コード"]))