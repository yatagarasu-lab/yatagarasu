from flask import Flask, request, jsonify, render_template
from services.dropbox_handler import handle_dropbox_webhook
from yatagarasu import analyze_latest_file
from scheduler import start_scheduler  # 自動解析スケジューラー
import os

app = Flask(__name__)

# Web表示：トップページ
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Dropbox Webhook検証（GETリクエストに対して challenge を返す）
@app.route('/webhook', methods=['GET', 'POST'])
def dropbox_webhook():
    if request.method == "GET":
        # Dropboxが送信する challenge をそのまま返す
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        if request.headers.get('X-Dropbox-Signature'):
            return handle_dropbox_webhook(request)
        return 'Ignored', 200

# GPTによる解析を実行するエンドポイント（手動）
@app.route("/analyze", methods=["GET"])
def analyze():
    result = analyze_latest_file()
    return result

# LINE BOT Webhook受信用エンドポイント（必要に応じて拡張）
@app.route("/line", methods=["POST"])
def line_webhook():
    # ここに LINE Messaging API の処理を書く（未実装ならOK）
    return "LINE Bot: OK", 200

if __name__ == '__main__':
    start_scheduler()  # APSchedulerを起動（5分おきなど）
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)