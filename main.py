import os
import tempfile
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import dropbox

# LINE設定（環境変数から）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
USER_ID = os.getenv("LINE_USER_ID")  # Push通知送信用（必要なら）
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

app = Flask(__name__)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("[Webhook受信] リクエスト内容:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Check channel secret and access token.")
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_text = event.message.text
    print("[テキスト受信]", user_text)

    # Dropbox保存
    file_path = os.path.join(tempfile.gettempdir(), "received_text.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(user_text)

    dropbox_path = f"{DROPBOX_FOLDER}/texts/{event.timestamp}.txt"
    with open(file_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

    print(f"[Dropboxアップロード] {dropbox_path}")
    reply_message = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    print("[画像受信] メッセージID:", event.message.id)

    message_content = line_bot_api.get_message_content(event.message.id)
    temp_path = os.path.join(tempfile.gettempdir(), f"{event.message.id}.jpg")
    
    with open(temp_path, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

    print(f"[画像保存] {temp_path}")

    # Dropboxへアップロード
    dropbox_path = f"{DROPBOX_FOLDER}/images/{event.message.id}.jpg"
    with open(temp_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
    
    print(f"[Dropboxアップロード] {dropbox_path}")
    
    # GPTで分析などの処理（ここに追加可能）
    print("[GPT処理] 処理ロジックはここに追加できます")

    reply_message = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_message))

if __name__ == "__main__":
    app.run()