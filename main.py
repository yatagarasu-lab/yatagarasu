from flask import Flask, request
import openai
import os

app = Flask(__name__)

# OpenAI クライアント初期化（v1）
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/callback", methods=["POST"])
def callback():
    user_message = "こんにちは！"

    # 応答を生成
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたは親切なアシスタントです。"},
            {"role": "user", "content": user_message}
        ]
    )

    reply_text = response.choices[0].message.content
    print(reply_text)

    return "ありがとうございます"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)