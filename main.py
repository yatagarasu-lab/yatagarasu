from flask import Flask, request, jsonify
from dropbox_handler import handle_dropbox_event
import os

app = Flask(__name__)

@app.route("/")
def index():
    return "OK", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox webhook verification
        challenge = request.args.get("challenge")
        return challenge, 200
    elif request.method == "POST":
        # Dropbox webhook event
        handle_dropbox_event()
        return "Webhook received", 200

if __name__ == "__main__":
    app.run(debug=True)