from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "🟢 GPT解析BOTは待機中です"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropboxからの確認用 Challenge 応答
        challenge = request.args.get("challenge")
        return challenge if challenge else "No challenge found", 200
    elif request.method == "POST":
        print("📩 Webhook POST received from Dropbox")
        return "Webhook received", 200

if __name__ == "__main__":
    app.run()