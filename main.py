from flask import Flask, request
from analyze_and_notify import analyze_dropbox_updates

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Dropbox Webhook is running!"

@app.route("/webhook", methods=["POST"])
def webhook():
    # Dropbox からの変更通知に反応して解析処理を実行
    analyze_dropbox_updates()
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)