from flask import Flask, request, jsonify, render_template
from services.dropbox_handler import handle_dropbox_webhook
from yatagarasu import analyze_latest_file  # 解析ロジックを外部モジュールに分離
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')  # templates/index.html が必要（無ければプレーンテキストにしてもOK）

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('X-Dropbox-Signature'):
        return handle_dropbox_webhook(request)
    return 'Ignored', 200

@app.route('/analyze', methods=['GET'])
def analyze():
    result = analyze_latest_file()
    return result

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))  # Render用にPORT対応
    app.run(host="0.0.0.0", port=port)