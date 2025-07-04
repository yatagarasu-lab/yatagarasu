import os
from flask import Flask, request
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from gpt_utils import process_with_gpt_text, process_with_gpt_image
from dropbox_handler import upload_zip_to_dropbox, find_and_remove_duplicates

load_dotenv()

# 環境変数の読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")
PORT = int(os.getenv("PORT", 10000))

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

app = Flask(__name__)

@app.route("/")
def index():
    return "LINE-GPT-Dropbox Bot is running."

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"エラー: {e}")
    return 'OK'

# テキストメッセージの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    if event.source.user_id != LINE_USER_ID:
        return

    text = event.message.text.strip()
    response_text = process_with_gpt_text(text)

    # 保存＆圧縮してDropboxへ送信
    filename = "text_summary.txt"
    upload_zip_to_dropbox(filename, text.encode(), "スロットデータ")

    # LINEに返信
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

# 画像メッセージの処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    if event.source.user_id != LINE_USER_ID:
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = b"".join(chunk for chunk in message_content.iter_content())

    # GPTで画像解析
    response_text = process_with_gpt_image(image_data)

    # 保存＆圧縮してDropboxへ送信
    filename = "image_summary.jpg"
    upload_zip_to_dropbox(filename, image_data, "スロットデータ")

    # LINEに返信
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

# 起動
if __name__ == "__main__":
    find_and_remove_duplicates("/Apps/slot-data-analyzer")
    app.run(host="0.0.0.0", port=PORT)