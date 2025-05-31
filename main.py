from flask import Flask, request
from openai import OpenAI
import os

app = Flask(__name__)

# OpenAI クライアントの初期化（proxies は削除）
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

@app.route("/callback", methods=["POST"])
def callback():
    # 仮のユーザー入力（ここはLINEから受け取るように後で修正）
    user_message = "こんにちは！"

    # ChatGPT にメッセージ送信
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたは親切なアシスタントです。"},
            {"role": "user", "content": user_message}
        ]
    )

    reply_text = response.choices[0].message.content
    print(reply_text)  # コンソールに出力（動作確認用）

    return "ありがとうございます"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)