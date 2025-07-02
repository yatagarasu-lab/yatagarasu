from flask import Flask, request, jsonify
import hashlib
import os

app = Flask(__name__)

# Dropbox Challenge応答用 (Webhook確認)
@app.route("/webhook", methods=["GET"])
def verify_dropbox():
    challenge = request.args.get("challenge")
    return challenge, 200


# POSTリクエストでDropboxから通知が来たときの処理
@app.route("/webhook", methods=["POST"])
def dropbox_webhook():
    # Dropboxは変更通知だけ送ってくる（ファイル名などは別APIで取得が必要）
    print("🔔 Dropboxからファイル更新の通知が来ました")
    return "", 200


# Dropbox内のファイルを一覧 → 内容を取得 → 重複判定＆削除 → 残りを解析
from dropbox import Dropbox
from dotenv import load_dotenv

load_dotenv()

DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
DROPBOX_FOLDER = "/スロットデータ"  # 任意のDropboxフォルダ名

@app.route("/analyze", methods=["GET"])
def analyze_files():
    dbx = Dropbox(DROPBOX_ACCESS_TOKEN)
    entries = dbx.files_list_folder(DROPBOX_FOLDER).entries

    content_map = {}
    kept_files = []
    deleted_files = []

    for entry in entries:
        if not hasattr(entry, "path_lower"):
            continue

        metadata, res = dbx.files_download(entry.path_lower)
        content = res.content
        hash_val = hashlib.md5(content).hexdigest()

        if hash_val in content_map:
            dbx.files_delete_v2(entry.path_lower)
            deleted_files.append(entry.name)
        else:
            content_map[hash_val] = entry.name
            kept_files.append(entry.name)

    return jsonify({
        "kept_files": kept_files,
        "deleted_files": deleted_files,
        "total_checked": len(entries)
    })


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)