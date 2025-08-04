from flask import Flask, request
from services.dropbox_handler import handle_dropbox_webhook

app = Flask(__name__)

# Dropbox Webhookエンドポイント
@app.route("/dropbox-webhook", methods=["GET", "POST"])
def dropbox_webhook():
    return handle_dropbox_webhook(request)

# Render動作確認用
@app.route("/")
def index():
    return "🟢 YATAGARASU Webhook Server is running."

if __name__ == "__main__":
    app.run(debug=True, port=5000)