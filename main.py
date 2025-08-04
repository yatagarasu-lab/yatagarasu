from flask import Flask, request
from dropbox_integration import handle_dropbox_webhook

app = Flask(__name__)


@app.route("/", methods=["GET"])
def health_check():
    return "Server is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    print("✅ Dropbox webhook received.")
    return handle_dropbox_webhook()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)