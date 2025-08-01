from flask import Flask, request, jsonify

app = Flask(__name__)

# ── 基本ルート ─────────────────────
@app.route('/')
def index():
    return 'Webhook server is running on Render!'

# ── Dropbox Webhook受信用エンドポイント ───────
@app.route('/webhook', methods=['GET', 'POST'])
def handle_webhook():
    if request.method == 'GET':
        # Dropboxの確認用 (チャレンジ応答)
        challenge = request.args.get('challenge')
        return challenge if challenge else 'No challenge param', 200
    elif request.method == 'POST':
        # 通常の通知（ここに自動解析処理などを追加）
        print('Received Dropbox webhook POST')
        print(request.json)  # JSON内容をログ出力
        return 'OK', 200

# ── アプリ起動 ─────────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)