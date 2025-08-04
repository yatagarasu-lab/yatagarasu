# main.py

from flask import Flask, request, jsonify
import os
from processor import process_all_files
from log_utils import log

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "✅ Yatagarasu GPT解析BOT 動作中"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox Webhookの認証確認用（challengeパラメータを返す）
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        # Webhook通知が来た場合 → Dropbox内の全ファイルを処理
        log("📥 Dropbox Webhook受信、ファイル解析開始")
        process_all_files()
        return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)