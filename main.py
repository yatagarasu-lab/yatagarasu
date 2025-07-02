from flask import Flask, request, jsonify
import os
import dropbox

app = Flask(__name__)

# Dropboxの検証用トークン
VERIFY_TOKEN = os.getenv('DROPBOX_VERIFY_TOKEN')

# Dropbox API用のアクセストークン
DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')

# LINE返信用の関数（省略可能。LINE連携が不要なら削除）
def notify_line(message):
    print("LINE通知:", message)

# ✅ Dropbox Webhookの受信エンドポイント
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        challenge = request.args.get('challenge')
        return challenge, 200
    elif request.method == 'POST':
        print("Webhook POST受信:", request.json)
        notify_line("Dropboxに新しい変更がありました")
        return '', 200

# Renderで起動する用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))