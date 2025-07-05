from flask import Flask, request, abort
import os
from dotenv import load_dotenv
from dropbox_handler import handle_dropbox_event
from scheduler import start_scheduler

# 環境変数を読み込む（ローカル開発用）
load_dotenv()

app = Flask(__name__)

@app.route("/")
def index():
    return "📦 Dropbox × GPT 解析 BOT 稼働中"

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        try:
            body = request.json
            print("📥 Webhook 受信:", body)

            # Dropbox のイベントを処理
            handle_dropbox_event(body)
            return "✅ Webhook 受信", 200

        except Exception as e:
            print("❌ Webhook 処理エラー:", e)
            return "❌ エラー", 500
    else:
        abort(400)

if __name__ == "__main__":
    # Render上では gunicorn を使うが、ローカルではこれで起動可
    print("🚀 Flask サーバーを起動中...")
    start_scheduler()
    app.run(debug=True, port=5000)
