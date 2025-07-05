import os
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import dropbox
from io import BytesIO

app = Flask(__name__)

# LINEの環境変数
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

if not LINE_CHANNEL_SECRET or not LINE_CHANNEL_ACCESS_TOKEN:
    raise Exception("LINE環境変数が正しく設定されていません。")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropboxの環境変数
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

if not DROPBOX_REFRESH_TOKEN or not DROPBOX_APP_KEY or not DROPBOX_APP_SECRET:
    raise Exception("Dropboxの環境変数が正しく設定されていません。")

# Dropbox接続
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def is_duplicate(content, folder="/Apps/slot-data-analyzer"):
    hash_new = file_hash(content)
    try:
        res = dbx.files_list_folder(folder)
        for entry in res.entries:
            metadata, response = dbx.files_download(entry.path_lower)
            existing_content = response.content
            if file_hash(existing_content) == hash_new:
                return True
    except dropbox.exceptions.ApiError as e:
        print(f"Dropbox APIエラー: {e}")
    return False

@app.route("/")
def health_check():
    return "OK", 200

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    user_message = event.message.text
    reply = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_id = event.message.id
    content = line_bot_api.get_message_content(message_id)
    image_data = BytesIO(content.content)

    # 重複チェック
    if is_duplicate(image_data.getvalue()):
        print("重複画像：保存スキップ")
        return

    filename = f"/Apps/slot-data-analyzer/{message_id}.jpg"
    dbx.files_upload(image_data.getvalue(), filename)
    print(f"画像保存完了: {filename}")

    # LINE通知
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text="画像をDropboxに保存しました。ありがとうございます")
    )

if __name__ == "__main__":
    app.run()