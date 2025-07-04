# main.py
from flask import Flask, request, abort
import os
import hashlib
import hmac
import dropbox
from dotenv import load_dotenv
from dropbox_utils import handle_dropbox_event
from line_utils import push_message_to_line

load_dotenv()
app = Flask(__name__)

DROPBOX_SECRET = os.getenv("DROPBOX_APP_SECRET")

@app.route('/')
def health_check():
    return 'OK', 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        challenge = request.args.get('challenge')
        return challenge, 200

    signature = request.headers.get('X-Dropbox-Signature')
    if not verify_dropbox_signature(request.data, signature):
        abort(403)

    # Dropbox イベントを処理
    handle_dropbox_event()

    # LINEへ通知（任意）
    push_message_to_line("新しいファイルがDropboxに追加されました。解析を開始します。")

    return '', 200

def verify_dropbox_signature(data, signature):
    computed_signature = hmac.new(
        DROPBOX_SECRET.encode('utf-8'),
        data,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_signature, signature)

if __name__ == '__main__':
    app.run(debug=True)