import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import dropbox

app = Flask(__name__)

# 環境変数の取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")

# LINE Botの初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# LINEユーザーID（あなた専用）
LINE_USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"

# LINE Webhookの受信エンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        abort(400)
    return 'OK'

# メッセージ受信時の処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply_text = "ありがとうございます"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# LINE Push通知送信関数
def push_to_line(text):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
        return "✅ LINE通知成功"
    except Exception as e:
        return f"❌ LINE通知失敗: {str(e)}"

# LINE通知テスト用エンドポイント
@app.route("/push-test")
def push_test():
    return push_to_line("📦 Dropbox連携テスト中です！")

# Dropboxアップロードテストエンドポイント
@app.route("/dropbox-test")
def dropbox_test():
    try:
        dbx = dropbox.Dropbox(DROPBOX_TOKEN)
        content = "これはDropboxへの自動アップロードのテストです。"
        path = "/Apps/slot-data-analyzer/スロット/GPT_アップロードテスト.txt"
        dbx.files_upload(content.encode(), path, mode=dropbox.files.WriteMode.overwrite)
        push_to_line("✅ Dropboxアップロード成功！ファイルを確認してください。")
        return "✅ Dropboxへのアップロード成功！"
    except Exception as e:
        push_to_line(f"❌ Dropboxアップロード失敗: {str(e)}")
        return f"❌ アップロード失敗: {str(e)}"

# 起動確認用
@app.route("/")
def home():
    return "✅ LINE BOT + Dropbox連携サーバー 起動中"