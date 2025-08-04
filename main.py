# main.py

from flask import Flask, request, jsonify
import os
from gpt_summarizer import summarize_file
from dropbox_handler import get_new_files

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "📦 Dropbox × GPT API is running"

# Dropbox Webhook確認用（必須）
@app.route("/dropbox-webhook", methods=["GET"])
def verify_dropbox():
    return request.args.get("challenge")

# Dropbox Webhookが発火したときに呼ばれるPOSTハンドラ
@app.route("/dropbox-webhook", methods=["POST"])
def handle_dropbox_webhook():
    print("📥 Dropbox Webhook 発火")

    # 新規ファイルのみ取得
    new_files = get_new_files()

    for filename, content in new_files:
        print(f"🧠 GPT処理中: {filename}")
        summary = summarize_file(filename, content)
        print(f"✅ 要約結果: {summary}")

    return "", 200

# ローカル確認用（手動テスト用）
@app.route("/test", methods=["GET"])
def test_dropbox_trigger():
    new_files = get_new_files()
    results = []

    for filename, content in new_files:
        summary = summarize_file(filename, content)
        results.append({"file": filename, "summary": summary})

    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)