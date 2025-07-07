from flask import Flask, request, abort
import os
import json
import traceback
import requests
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dropbox import Dropbox

app = Flask(__name__)

# 環境変数の取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
LINE_USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"

# LINEインスタンス
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# アクセストークン取得関数（毎回自動更新）
def get_dropbox_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# Webhookエンドポイント
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge", "")
        print("✅ Dropbox webhook検証（GET）:", challenge)
        return str(challenge), 200

    if request.method == "POST":
        try:
            print("📩 Dropbox Webhook通知を受信:")
            payload = request.get_json(silent=True)
            print("📦 Payload (JSON):", json.dumps(payload, indent=2) if payload else "⚠️ JSONなし")

            # Dropboxアクセストークンを取得して接続
            access_token = get_dropbox_access_token()
            dbx = Dropbox(access_token)

            folder_path = "/Apps/slot-data-analyzer"
            entries = dbx.files_list_folder(folder_path).entries
            if not entries:
                line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text="📂 新しいファイルが見つかりません"))
                return "", 200

            # 最新ファイル取得（最終更新日時でソート）
            entries.sort(key=lambda x: x.server_modified if hasattr(x, "server_modified") else None, reverse=True)
            latest = entries[0]
            file_path = latest.path_display

            # ファイル取得と中身の抽出
            metadata, res = dbx.files_download(file_path)
            content = res.content.decode("utf-8", errors="ignore")
            preview = content[:300] + ("..." if len(content) > 300 else "")

            # LINE通知送信
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(
                    text=f"📥 Dropboxにファイルが追加・更新されました！\n\n🗂️ ファイル名：{latest.name}\n📄 内容抜粋：\n{preview}"
                )
            )

            return "", 200

        except Exception as e:
            print("❌ Webhookエラー:", str(e))
            traceback.print_exc()
            try:
                line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=f"⚠ Webhookエラー: {str(e)}"))
            except Exception as notify_err:
                print("❌ LINE通知失敗:", notify_err)
            return "Internal Server Error", 500

# LINEのメッセージ受信エンドポイント
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
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

if __name__ == "__main__":
    app.run()