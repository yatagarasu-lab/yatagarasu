from flask import Flask, request

app = Flask(__name__)

# ホームページ
@app.route('/')
def home():
    return 'Hello from Render!'

# LINEなどのWebhook用
@app.route('/callback', methods=['POST'])
def callback():
    # POSTデータのログ出力（必要なら）
    print("Received callback:", request.json)
    return 'Callback received', 200

# Dropbox動作確認用
@app.route('/dropbox-test')
def dropbox_test():
    return 'Dropbox test OK', 200

# アプリを起動
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)