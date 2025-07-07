from flask import Flask, request, abort
import os
import json
import traceback
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropboxが送る challenge を文字列で返す（Noneでも空文字で返す）
        challenge = request.args.get("challenge", "")
        print("✅ Webhook検証（GET）:", challenge)
        return str(challenge), 200

    if request.method == "POST":
        try:
            raw_data = request.get_data(as_text=True)
            print("📩 Dropbox Webhook通知を受信:")
            print(raw_data)

            # JSONとしてパース（安全なパース）
            payload = request.get_json(silent=True)
            print("📦 Payload (JSON):", json.dumps(payload, indent=2) if payload else "⚠️ JSONなし")

            # LINE通知（テスト用）
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text="📥 Dropboxにファイルが追加または更新されました")
            )

            return "", 200
        except Exception as e:
            print("❌ Webhookエラー:", str(e))
            traceback.print_exc()

            try:
                line_bot_api.push_message(
                    LINE_USER_ID,
                    TextSendMessage(text=f"⚠ Webhookエラー: {str(e)}")
                )
            except Exception as notify_err:
                print("❌ LINE通知失敗:", notify_err)

            return "Internal Server Error", 500

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("💬 LINE Message:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="ありがとうございます")
    )

if __name__ == "__main__":
    app.run()