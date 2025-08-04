from flask import Flask, request, render_template
from services.dropbox_handler import handle_dropbox_webhook
from services.line_handler import handle_line_webhook
from yatagarasu import analyze_latest_file
import os

app = Flask(__name__)

# トップページ
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Dropbox Webhook 受信
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

# LINE BOT Webhook受信
@app.route("/line", methods=["POST"])
def line_webhook():
    return handle_line_webhook(request)

# ローカル用起動設定（Renderでは不要）
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)