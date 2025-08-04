from flask import Blueprint, request, make_response
from services.dropbox_handler import process_dropbox_delta

dropbox_webhook = Blueprint('dropbox_webhook', __name__)

# Dropbox の webhook ルート
@dropbox_webhook.route('/webhook/dropbox', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        # webhook 検証用 (Dropbox が challenge を送ってくる)
        challenge = request.args.get('challenge')
        return make_response(challenge, 200)

    if request.method == 'POST':
        # 実際のファイル更新通知を処理
        data = request.get_json()
        if not data:
            return "No payload", 400

        # Dropbox 側の通知に含まれるユーザーごとの更新を処理
        for account in data.get('list_folder', {}).get('accounts', []):
            process_dropbox_delta(account_id=account)

        return "Webhook received", 200
