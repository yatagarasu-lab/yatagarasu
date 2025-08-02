import os
from flask import Flask, request
import dropbox
from datetime import datetime

app = Flask(__name__)

# Dropbox 認証情報（Render の環境変数から取得）
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")  # ※リフレッシュトークン方式にする場合は後述

# ログファイルのパス
LOG_FILE = "gpt_log.txt"

# Dropbox にアップロードするパス
DROPBOX_UPLOAD_PATH = "/gpt_log.txt"


def write_gpt_log(content: str):
    """ローカルにログを追記し、Dropboxにアップロード"""
    # ファイルがなければ作成
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write("")

    # ログを追記
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        f.write(f"{timestamp} {content}\n")

    # Dropbox にアップロード
    upload_to_dropbox(LOG_FILE, DROPBOX_UPLOAD_PATH)


def upload_to_dropbox(local_path: str, dropbox_path: str):
    """Dropboxへファイルをアップロード"""
    if not DROPBOX_ACCESS_TOKEN:
        print("Dropbox アクセストークンが設定されていません")
        return

    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
        print(f"✅ Dropbox にアップロードしました: {dropbox_path}")


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        content = request.json.get("message", "（内容なし）")
        write_gpt_log(content)
        return {"status": "success", "message": "GPTログを記録＆Dropboxに保存しました"}

    return "GPTログ記録システムは動作中です（GET）"


if __name__ == "__main__":
    app.run(debug=True)