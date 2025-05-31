from flask import Flask, request
from openai import OpenAI
import os

app = Flask(__name__)

# OpenAI クライアントの初期化（v1.22対応）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/callback", methods=["POST"])
def callback():
    # ユーザーメッセージを仮置き（実装時はLINEメッセージを取得）
    user_message = "こんにちは！"

    # OpenAI へのリクエスト（v1形式）
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたは親切なアシスタントです。"},
            {"role": "user", "content": user_message}
        ]
    )

    # 応答文を取り出す
    reply_text = response.choices[0].message.content
    print(reply_text)  # デバッグ出力

    return "ありがとうございます"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)