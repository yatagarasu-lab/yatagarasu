import os
import json
import openai
import dropbox
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from google.cloud import vision
from werkzeug.utils import secure_filename

# --- 環境変数の読み込み ---
DROPBOX_REFRESH_TOKEN = os.environ["DROPBOX_REFRESH_TOKEN"]
DROPBOX_CLIENT_ID = os.environ["DROPBOX_CLIENT_ID"]
DROPBOX_CLIENT_SECRET = os.environ["DROPBOX_CLIENT_SECRET"]
LINE_CHANNEL_ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
LINE_CHANNEL_SECRET = os.environ["LINE_CHANNEL_SECRET"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
GOOGLE_CLOUD_VISION_KEY = os.environ["GOOGLE_CLOUD_VISION_KEY"]

# --- クライアント初期化 ---
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY
vision_client = vision.ImageAnnotatorClient.from_service_account_json(GOOGLE_CLOUD_VISION_KEY)

# --- Flask アプリケーション ---
app = Flask(__name__)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたはDropboxとLINE Botを使ったファイル解析エージェントです。"},
            {"role": "user", "content": user_text}
        ]
    )
    reply = response.choices[0].message.content
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@app.route("/dropbox-webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge")
    elif request.method == "POST":
        # ここにDropboxのファイル解析処理を書く
        print("Dropboxファイル変更を検知しました。")
        return "OK"

# --- メイン関数 ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))