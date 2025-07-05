from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
from gpt_handler import analyze_zip_content, analyze_image_content
from dropbox_handler import save_uploaded_file, download_file
import os

app = Flask(__name__)

# LINE設定
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
USER_ID = os.getenv("LINE_USER_ID")  # 自分のLINE ID（Push用）

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"エラー: {e}")
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text

    # Dropboxに保存
    file_path = save_uploaded_file(text.encode("utf-8"), extension="txt")

    # GPTで解析
    result = analyze_zip_content(text.encode("utf-8"))  # ZIPと同じ解析を再利用

    # LINE通知（ユーザー宛）
    line_bot_api.push_message(USER_ID, TextSendMessage(text=result[:4000]))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # 画像データ取得
    message_id = event.message.id
    content = line_bot_api.get_message_content(message_id).content

    # Dropbox保存
    file_path = save_uploaded_file(content, extension="jpg")

    # GPT画像解析
    result = analyze_image_content(content)

    # LINE通知
    line_bot_api.push_message(USER_ID, TextSendMessage(text=result[:4000]))

@app.route("/dropbox_webhook", methods=["POST"])
def handle_dropbox_webhook():
    try:
        # 変更通知を受けたファイルを処理
        path = "/Apps/slot-data-analyzer/latest_upload.zip"
        zip_data = download_file(path)

        result = analyze_zip_content(zip_data)
        line_bot_api.push_message(USER_ID, TextSendMessage(text=result[:4000]))
        return "OK", 200

    except Exception as e:
        print(f"Dropbox Webhookエラー: {e}")
        line_bot_api.push_message(USER_ID, TextSendMessage(text=f"⚠️ Webhookでエラー: {e}"))
        return abort(500)

if __name__ == "__main__":
    app.run()