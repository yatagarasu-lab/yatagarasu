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
        # Dropbox Webhook検証用 (challenge)
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        # Webhookが通知されたらファイルをスキャン
        entries = dbx.files_list_folder(DROPBOX_FOLDER, recursive=True).entries
        for entry in entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                _, ext = os.path.splitext(entry.name)
                if ext.lower() in [".txt", ".csv", ".xlsx", ".json", ".jpg", ".jpeg", ".png"]:
                    _, res = dbx.files_download(entry.path_display)
                    content = res.content

                    if is_duplicate(content):
                        dbx.files_delete_v2(entry.path_display)
                    else:
                        result = analyze_file(content, entry.name)
                        notify_line(f"✅新規ファイル解析結果\n📄{entry.name}\n\n{result}")
        return "OK", 200