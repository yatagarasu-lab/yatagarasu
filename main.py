# main.py

from flask import Flask, request
from services.dropbox_handler import handle_dropbox_webhook
from services.line_handler import handle_line_request
from services.gpt_summarizer import summarize_file_and_notify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "YATAGARASU BOT is running"

# Dropbox Webhook受信エンドポイント
@app.route("/webhook", methods=["POST"])
def dropbox_webhook():
    return handle_dropbox_webhook()

# Dropbox Webhook検証（GETリクエスト）
@app.route("/webhook", methods=["GET"])
def verify_dropbox_webhook():
    challenge = request.args.get("challenge")
    return challenge if challenge else "Missing challenge", 400

# LINE Webhook受信エンドポイント
@app.route("/callback", methods=["POST"])
def line_callback():
    return handle_line_request()

# 動作テスト用のGPT要約手動実行エンドポイント（任意）
@app.route("/summarize_test", methods=["POST"])
def summarize_test():
    folder_path = request.args.get("path", "/Apps/slot-data-analyzer")
    summarize_file_and_notify(folder_path)
    return "Summarization Triggered", 200

if __name__ == "__main__":
    app.run()