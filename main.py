from flask import Flask, request, abort
import os
import json
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from dropbox_utils import list_files  # ← Dropbox操作関数を読み込み

app = Flask(__name__)

# LINEチャンネル設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"  # あなたのLINEユーザーID

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox Webhook エンドポイント
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox webhook 検証用（最初の登録時に必要）
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        try:
            print("📩 Dropbox Webhook受信")
            payload = request.get_data(as_text=True)
            print("受信データ:", payload)

            # 最新ファイルの一覧取得
            files = list_files()
            filenames = [f.name for f in files]
            file_list_text = "\n".join(filenames) if filenames else "ファイルが見つかりませんでした"

            # LINEにPush通知送信
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text=f"📦 Dropboxに変更がありました\n最新ファイル一覧:\n{file_list_text}")
            )

            return "", 200
        except Exception as e:
            print(f"Webhook処理エラー: {e}")
            return "Error", 500

# LINE Bot Webhook エンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("LINEメッセージ受信:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# LINEメッセージイベント処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run()