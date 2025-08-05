# main.py（Yatagarasu）

from flask import Flask, request
from update_code import handle_code_update

app = Flask(__name__)

@app.route("/")
def index():
    return "Yatagarasu is running!"

# E.T Codeからコードを受信するエンドポイント
@app.route("/update-code", methods=["POST"])
def update_code():
    return handle_code_update()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)