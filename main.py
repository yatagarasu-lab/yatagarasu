from flask import Flask
app = Flask(__name__)

@app.route("/")
def index():
    return "✅ 動作確認OK！Flaskアプリが起動しています。"

if __name__ == "__main__":
    app.run()