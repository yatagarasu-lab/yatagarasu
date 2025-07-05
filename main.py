# main.py
import os
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)
from linebot.v3.exceptions import InvalidSignatureError
from processor import process_files
from dropbox_handler import upload_to_dropbox

app = Flask(__name__)

# LINE Bot 設定
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
user_id = os.getenv("LINE_USER_ID")

if channel_secret is None or channel_access_token is None:
    raise Exception("LINEの環境変数が設定されていません。")

configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# LINE webhook エンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# メッセージ処理
@handler.add(event=WebhookParser)
def handle_message(event):
    # POSTされたデータがメッセージイベントか確認
    if event.message and hasattr(event.message, 'text'):
        message_text = event.message.text

        # ユーザーの送信内容をDropboxに保存
        filename = f"message_{event.timestamp}.txt"
        upload_to_dropbox(filename, message_text)

        # 返信（固定文）
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            reply = ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text="ありがとうございます")]
            )
            line_bot_api.reply_message(reply)

# Renderからの手動実行ポイント
@app.route("/manual-process", methods=["GET"])
def manual_process():
    process_files()
    return "Manual processing complete."

if __name__ == "__main__":
    app.run()