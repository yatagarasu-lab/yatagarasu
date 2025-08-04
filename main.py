from flask import Flask, request, jsonify, render_template
from services.dropbox_handler import handle_dropbox_webhook
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def webhook():
    if request.headers.get('X-Dropbox-Signature'):
        return handle_dropbox_webhook(request)
    return 'Ignored', 200

if __name__ == '__main__':
    app.run(debug=True)