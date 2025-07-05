import os
from flask import Flask, request
from dotenv import load_dotenv
from dropbox_handler import handle_dropbox_webhook
from analyze_file import analyze_file
from line_push import send_line_message

# 環境変数の読み込み
load_dotenv()

app = Flask(__name__)

# Dropbox Webhook 用のルート
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge")
    elif request.method == "POST":
        # Dropbox Webhook からの通知処理
        handle_dropbox_webhook(request)
        return '', 200

# 手動テスト用ルート（任意で後ほど削除してOK）
@app.route("/test", methods=["GET"])
def test():
    test_path = "/Apps/slot-data-analyzer/testfile.txt"
    try:
        result = analyze_file(test_path)
        send_line_message(f"✅ テスト解析完了: {os.path.basename(test_path)}\n\n{result[:300]}...")
        return "✅ テスト完了", 200
    except Exception as e:
        return f"❌ エラー: {e}", 500

if __name__ == "__main__":
    app.run(debug=True)