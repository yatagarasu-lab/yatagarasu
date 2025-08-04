# main.py（完全版）📦 Render × GitHub × Dropbox × GPT × LINE webhook連携構成
from flask import Flask, request
from dropbox_handler import handle_dropbox_webhook
from line_handler import handle_line_webhook
from gpt_summarizer import summarize_from_dropbox  # 必要に応じて使用

app = Flask(__name__)

# ヘルスチェック用
@app.route("/", methods=["GET"])
def index():
    return "Yatagarasu AI Bot is running."

# Dropbox webhook 用エンドポイント
@app.route("/dropbox_webhook", methods=["POST"])
def dropbox_webhook():
    return handle_dropbox_webhook()

# LINE webhook 用エンドポイント
@app.route("/callback", methods=["POST"])
def line_callback():
    return handle_line_webhook()

# 必要であればGPT直接実行テスト用エンドポイント（任意）
@app.route("/test_summarize", methods=["POST"])
def test_gpt_summary():
    return summarize_from_dropbox()

if __name__ == "__main__":
    app.run(debug=True)