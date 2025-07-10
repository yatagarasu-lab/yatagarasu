import os
from flask import Flask, request, Response
from dotenv import load_dotenv
from main import process_dropbox_change

load_dotenv()

app = Flask(__name__)

@app.route('/webhook', methods=['GET'])
def verify():
    challenge = request.args.get('challenge')
    return Response(challenge, status=200)

@app.route('/webhook', methods=['POST'])
def webhook():
    # Dropboxのファイル更新通知を受信したら処理開始
    process_dropbox_change()
    return Response(status=200)

if __name__ == '__main__':
    app.run()