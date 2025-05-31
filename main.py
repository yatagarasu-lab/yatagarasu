from flask import Flask, request
from openai import OpenAI
import os

app = Flask(__name__)

# OpenAIクライアントの初期化（最新版対応）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/callback", methods=["POST"])
def callback():
    # ユーザーからのメッセージ（ここでは仮のメッセージ）
    user_message = "こんにちは！"

    # OpenAIから応答を取得
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたは親切なアシスタントです。"},
            {"role": "user", "content": user_message}
        ]
    )

    # 応答メッセージを取得
    reply_text = response.choices[0].message.content
    print(reply_text)  # 確認用ログ出力

    return "ありがとうございます"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)