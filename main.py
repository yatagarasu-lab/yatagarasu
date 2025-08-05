from flask import Flask, request, jsonify
from dropbox_integration import handle_dropbox_webhook
from dropbox_utils import read_log_file
from line_notifier import send_line_message
import os

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Yatagarasu (八咫烏) Webhook Server is running!"

# Dropbox Webhook
@app.route("/dropbox", methods=["GET", "POST"])
def dropbox_webhook():
    return handle_dropbox_webhook()

# Dropboxログ確認
@app.route("/read-log", methods=["GET"])
def read_log():
    file_path = request.args.get("path", "/logs/webhook_log.txt")
    content = read_log_file(file_path)
    return jsonify({
        "file": file_path,
        "content": content
    })

# 🔧 E.T Code → 八咫烏へのコード更新エンドポイント
@app.route("/update-code", methods=["POST"])
def update_code():
    data = request.get_json()
    filename = data.get("filename")
    code = data.get("code")

    if not filename or not code:
        return jsonify({"error": "filename and code are required"}), 400

    try:
        # ファイル書き換え（同ディレクトリ or 相対パスに注意）
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)

        # LINE通知（オプション）
        send_line_message(f"🛠 コードファイル '{filename}' が E.T Code から更新されました。")

        return jsonify({"status": "success", "message": f"{filename} updated"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    print("🔁 Flask App 起動中")
    app.run(host="0.0.0.0", port=10000)