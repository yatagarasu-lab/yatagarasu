from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# Flaskアプリ起動
app = Flask(__name__)

# LINE設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAI設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Dropbox Webhookエンドポイント
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        if challenge:
            return challenge, 200
        else:
            return "No challenge found", 400
    if request.method == "POST":
        print("✅ Dropbox webhook received!")
        return "", 200

# ✅ LINE callbackエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ✅ LINEメッセージ応答処理（OpenAI連携）
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # ChatGPTで応答生成
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # 必要に応じて "gpt-4"
        messages=[
            {"role": "user", "content": user_message}
        ]
    )

    reply_text = response["choices"][0]["message"]["content"]

    # LINEへ返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# ✅ アプリ起動
if __name__ == "__main__":
    app.run()