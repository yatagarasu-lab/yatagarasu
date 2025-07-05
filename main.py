from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import (
    MessageEvent,
    TextMessage,
    ImageMessage,
    TextSendMessage,
)
from dropbox_handler import download_file, upload_file_from_bytes
from gpt_handler import analyze_zip_content, analyze_text, analyze_image

import os
import datetime

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
USER_ID = os.getenv("LINE_USER_ID")


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"Callbackエラー: {e}")
        return "Error", 400

    return "OK", 200


@app.route("/dropbox_webhook", methods=["POST"])
def handle_dropbox_webhook():
    try:
        path = "/Apps/slot-data-analyzer/latest_upload.zip"
        zip_data = download_file(path)
        result = analyze_zip_content(zip_data)

        line_bot_api.push_message(USER_ID, TextSendMessage(text=result[:4000]))
        return "OK", 200

    except Exception as e:
        print(f"Webhookエラー: {e}")
        line_bot_api.push_message(
            USER_ID, TextSendMessage(text=f"⚠️ Webhook解析中にエラー発生: {e}")
        )
        return abort(500)


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    try:
        user_message = event.message.text
        result = analyze_text(user_message)
        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=result[:4000])
        )
    except Exception as e:
        print(f"テキスト解析エラー: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="⚠️ テキスト解析中にエラーが発生しました。"),
        )


@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    try:
        message_id = event.message.id
        message_content = line_bot_api.get_message_content(message_id)
        image_bytes = b"".join(chunk for chunk in message_content.iter_content())

        # 日付付きファイル名でDropboxに保存
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dropbox_path = f"/Apps/slot-data-analyzer/line_uploads/image_{timestamp}.jpg"
        upload_file_from_bytes(dropbox_path, image_bytes)

        # GPTで画像解析
        result = analyze_image(image_bytes)

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=result[:4000])
        )

    except Exception as e:
        print(f"画像処理エラー: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="⚠️ 画像の解析中にエラーが発生しました。"),
        )


if __name__ == "__main__":
    app.run()