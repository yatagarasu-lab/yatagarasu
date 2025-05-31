from flask import Flask, request
from openai import OpenAI
import os

app = Flask(__name__)

# OpenAIクライアントの初期化（v1方式）
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/callback", methods=["POST"])
def callback():
    # ユーザーからのメッセージを仮で定義（ここは適宜処理してください）
    user_message = "こんにちは！"

    # OpenAIの応答を生成
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "あなたは親切なアシスタントです。"},
            {"role": "user", "content": user_message}
        ]
    )

    # 応答のメッセージを取得
    reply_text = response.choices[0].message.content
    print(reply_text)  # 動作確認用にコンソール出力

    return "ありがとうございます"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)