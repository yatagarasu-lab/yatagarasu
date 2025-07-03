from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import openai
import os
from dotenv import load_dotenv

load_dotenv()

# Flaskアプリ起動
app = Flask(__name__)

# LINE Bot API設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# OpenAI設定
openai.api_key = os.getenv("OPENAI_API_KEY")

# ✅ Dropbox Webhookエンドポイント（GET確認用も含む）
@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge")  # Dropbox認証確認
    if request.method == "POST":
        print("Dropbox Webhook received.")
        return "", 200

# ✅ LINE Messaging APIエンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")

    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ✅ メッセージ受信イベント処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # GPT応答生成（例）
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",  # または "gpt-4"
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    gpt_reply = response["choices"][0]["message"]["content"]

    # LINEへ返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=gpt_reply)
    )

# ✅ アプリ起動
if __name__ == "__main__":
    app.run()