from flask import Flask, request, abort

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "OK", 200  # 動作確認用

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        body = request.get_data(as_text=True)
        print(f"Received webhook body: {body}")
        return "OK", 200
    except Exception as e:
        print(f"Error in webhook: {e}")
        abort(500)

if __name__ == "__main__":
    app.run()