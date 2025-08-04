from flask import Flask, request
from duplicate_cleaner import find_duplicates

app = Flask(__name__)

@app.route("/dropbox-webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge", "no challenge"), 200

    if request.method == "POST":
        try:
            duplicates = find_duplicates()
            print(f"重複ファイル一覧: {duplicates}")
            return "OK", 200
        except Exception as e:
            print(f"エラー: {e}")
            return "ERROR", 500

    return "Unsupported method", 405

if __name__ == "__main__":
    app.run(debug=True)