import os
from flask import Flask, request
from dropbox_integration import handle_dropbox_webhook

app = Flask(__name__)

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

@app.route("/", methods=["GET"])
def health_check():
    return "Yatagarasu is live!", 200

@app.route("/webhook", methods=["POST"])
def webhook():
    return handle_dropbox_webhook()