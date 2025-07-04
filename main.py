from flask import Flask, request, Response
from analyze_and_notify import analyze_new_files, find_and_remove_duplicates

app = Flask(__name__)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # DropboxからのWebhook通知受信時に実行される
    if request.method == "GET":
        return request.args.get("challenge")

    if request.method == "POST":
        # 1. 重複削除
        find_and_remove_duplicates()
        # 2. 新しいファイルの解析＋通知
        analyze_new_files()
        return Response("OK", status=200)

    return Response("Method Not Allowed", status=405)