from flask import Flask, request, jsonify, render_template
from services.dropbox_handler import handle_dropbox_webhook
from yatagarasu import analyze_latest_file
from scheduler import start_scheduler  # ← ここを追加
import os

app = Flask(__name__)

# Web表示：トップページ
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Webhook受信（Dropbox専用）
@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('X-Dropbox-Signature'):
        return handle_dropbox_webhook(request)
    return 'Ignored', 200

# GPTによる解析結果を返すエンドポイント
@app.route("/analyze", methods=["GET"])
def analyze():
    result = analyze_latest_file()
    return result

# LINE BOTエンドポイント（必要なら追加）
@app.route("/line", methods=["POST"])
def line_webhook():
    # ここに LINE BOT の処理を書く（未実装なら無視してOK）
    return "LINE Bot: OK", 200

if __name__ == '__main__':
    start_scheduler()  # ← 自動解析スケジューラーを起動
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)