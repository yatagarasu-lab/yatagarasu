from flask import Flask, request
from datetime import datetime
import openai
import os

from dropbox_client import upload_to_dropbox, read_from_dropbox  # ← 別ファイルで定義済み

app = Flask(__name__)

# GPTの応答処理
@app.route("/gpt", methods=["POST"])
def chat():
    user_input = request.json.get("message", "")
    if not user_input:
        return {"error": "message is required"}, 400

    # GPT応答
    openai.api_key = os.environ["OPENAI_API_KEY"]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "user", "content": user_input}
        ]
    )
    gpt_response = response.choices[0].message["content"]

    # ログをローカルファイルに保存
    log_entry = f"{datetime.now()} - {user_input} → {gpt_response}\n"
    with open("gpt_log.txt", "a", encoding="utf-8") as f:
        f.write(log_entry)

    # Dropboxにアップロード
    upload_to_dropbox("gpt_log.txt", "/GPTログ/gpt_log.txt")

    return {"response": gpt_response}

# ログをDropboxから読み込んで返す（確認用）
@app.route("/logs", methods=["GET"])
def logs():
    content = read_from_dropbox("/GPTログ/gpt_log.txt")
    return {"logs": content}

# 簡単なヘルスチェック
@app.route("/", methods=["GET"])
def root():
    return "GPT Logging Bot is live!"

if __name__ == "__main__":
    app.run()