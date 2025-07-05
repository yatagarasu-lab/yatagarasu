from flask import Flask, request, abort
import os
import dropbox
from dotenv import load_dotenv
from analyze_file import analyze_file
from line_push import send_line_message
from utils import is_duplicate, save_hash

# 環境変数の読み込み
load_dotenv()

# Flaskアプリ初期化
app = Flask(__name__)

# Dropbox クライアント初期化
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# LINE通知の有効化
LINE_PUSH_ENABLED = os.getenv("LINE_PUSH_ENABLED", "false").lower() == "true"

@app.route("/", methods=["GET"])
def health_check():
    return "✅ サーバー起動中"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if "list_folder" in data.get("delta", {}).get("users", {}):
        return "Ignored"

    # Dropboxから変更されたファイルの情報を取得
    if "path" in data:
        file_path = data["path"]
    elif "list_folder" in data.get("delta", {}):
        return "Delta mode not supported."
    else:
        return "Invalid webhook payload", 400

    try:
        metadata, res = dbx.files_download(file_path)
        content = res.content

        # 重複チェック
        if is_duplicate(content):
            return "✅ 重複ファイル（スキップ）", 200

        # 保存して処理済みに記録
        save_hash(content)

        # ファイル解析
        result = analyze_file(file_path)

        # LINE通知
        if LINE_PUSH_ENABLED:
            send_line_message(f"✅ 解析完了: {os.path.basename(file_path)}\n\n{result[:300]}...")

        return "✅ 処理成功", 200

    except Exception as e:
        return f"❌ エラー: {str(e)}", 500

if __name__ == "__main__":
    app.run(debug=True)
