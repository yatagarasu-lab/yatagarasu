from flask import Flask, request, abort

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "LINE Bot Webhook Server Running", 200

@app.route("/callback", methods=["POST"])
def callback():
    try:
        body = request.get_json()
        print("Received webhook payload:", body)
        return "OK", 200  # これが重要：LINEに200を返す！
    except Exception as e:
        print("Error handling webhook:", e)
        abort(400)

if __name__ == "__main__":
    app.run()