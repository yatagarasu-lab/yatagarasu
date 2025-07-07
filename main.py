from flask import Flask, request, abort
import os
import json
import traceback
import dropbox
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINEの設定
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ユーザーID（Push通知送信用）
LINE_USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"

# Dropbox 設定（リフレッシュトークン運用時は別途管理）
DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox の webhook 認証応答
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        try:
            print("📩 Dropbox からの通知を受信")

            # 通知内容を表示（確認ログ）
            raw_payload = request.get_data(as_text=True)
            print("📦 通知内容（raw）:\n", raw_payload)

            # JSON変換できればしておく
            try:
                parsed_payload = json.loads(raw_payload)
                print("✅ 通知内容（JSON）:\n", json.dumps(parsed_payload, indent=2))
            except Exception as je:
                print("⚠ JSONパースに失敗:", je)

            # 通知テスト用
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text="📥 Dropboxに変更がありました")
            )

            return '', 200

        except Exception as e:
            error_trace = traceback.format_exc()
            print("❌ Webhook処理中に例外発生:\n", error_trace)

            # エラー内容もLINEで通知（※無限ループ防止のため、必要なら条件追加）
            try:
                line_bot_api.push_message(
                    LINE_USER_ID,
                    TextSendMessage(text=f"⚠ Webhookエラー発生\n{str(e)}")
                )
            except Exception as line_error:
                print("❌ LINE通知にも失敗:", line_error)

            return 'Internal Server Error', 500

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("💬 LINEメッセージ受信:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    reply = "ありがとうございます"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()