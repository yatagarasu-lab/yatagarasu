# main.py（八咫烏）

from flask import Flask, request, jsonify
from dropbox_integration import handle_dropbox_webhook
from dropbox_utils import read_log_file  # ログ表示用
import os

app = Flask(__name__)

# トップページ
@app.route("/")
def index():
    return "Yatagarasu is running!"

# Dropbox Webhook
@app.route("/dropbox", methods=["GET", "POST"])
def dropbox_webhook():
    return handle_dropbox_webhook()

# Dropbox ログファイルの読み出しAPI（任意）
@app.route("/read-log", methods=["GET"])
def read_log():
    file_path = request.args.get("path", "/logs/webhook_log.txt")
    content = read_log_file(file_path)
    return jsonify({
        "file": file_path,
        "content": content
    })

# 🔥 E.T Code からコード受信して書き換えるエンドポイント
@app.route("/update-code", methods=["POST"])
def update_code():
    try:
        data = request.get_json()
        filename = data.get("filename")
        code = data.get("code")

        if not filename or not code:
            return jsonify({"error": "filename and code are required"}), 400

        # 実際にファイル書き換え
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)

        return jsonify({"status": "success", "updated_file": filename}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# アプリ起動
if __name__ == "__main__":
    print("Flask app 起動")
    app.run(host="0.0.0.0", port=10000)
    print("完了")