from flask import Flask, request, abort
import os
import json
import traceback
import dropbox
from io import BytesIO
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

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_MONITOR_FOLDER = "/Apps/slot-data-analyzer"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge", "")
        print("✅ Webhook検証（GET）:", challenge)
        return str(challenge), 200

    if request.method == "POST":
        try:
            # DropboxからのWebhook通知
            raw_data = request.get_data(as_text=True)
            print("📩 Dropbox Webhook通知を受信:")
            print(raw_data)

            payload = request.get_json(silent=True)
            if not payload:
                print("⚠️ JSONパース失敗")
                return "", 200

            # 対象のフォルダのファイル一覧を取得
            print("📂 Dropbox監視フォルダ:", DROPBOX_MONITOR_FOLDER)
            result = dbx.files_list_folder(DROPBOX_MONITOR_FOLDER)

            if not result.entries:
                line_bot_api.push_message(
                    LINE_USER_ID, TextSendMessage(text="📭 Dropboxにファイルがありません")
                )
                return "", 200

            # 最新ファイル（最後の1つ）を取得
            latest_file = result.entries[-1]
            file_path = latest_file.path_display
            file_name = latest_file.name
            print("📥 最新ファイル:", file_path)

            _, res = dbx.files_download(file_path)
            file_bytes = res.content

            # テキストファイルなら中身を読む
            if file_name.endswith((".txt", ".csv", ".json")):
                file_content = file_bytes.decode("utf-8")
                summary = summarize_text(file_content)
            else:
                summary = f"📎 新しいファイルが追加されました: {file_name}"

            # LINE通知
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text=summary)
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


def summarize_text(text):
    """ファイル内容を簡易的に要約"""
    lines = text.strip().splitlines()
    preview = "\n".join(lines[:10])  # 最初の10行を送る
    return f"📘 ファイル内容プレビュー:\n{preview}"


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