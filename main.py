from flask import Flask, request

app = Flask(__name__)

@app.route("/")
def index():
    return "✅ Flaskアプリは正常に動作しています！"

# 既存のWebhookやPush処理などもこの下に書かれているはずです
@app.route("/", methods=["GET"])
def home():
    return "Slot Data Analyzer Bot is running."