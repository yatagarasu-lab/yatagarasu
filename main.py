from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import os
import dropbox
from datetime import datetime
from gpt_logic import analyze_and_save
from dropbox_handler import save_to_dropbox
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# LINE API
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

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
def handle_text_message(event):
    text = event.message.text
    user_id = event.source.user_id

    # スロット以外はGPTとやり取りをDropboxへ保存
    save_to_dropbox(text.encode(), f"/会話記録/{datetime.now().isoformat()}_{user_id}.txt")
    analyze_and_save(text, is_image=False)

    # 返信（固定）
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text="ありがとうございます")
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    message_id = event.message.id

    # LINE画像を取得
    message_content = line_bot_api.get_message_content(message_id)
    image_data = b''.join(chunk for chunk in message_content.iter_content())

    # Dropboxに保存（スロット画像専用）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dropbox_path = f"/スロットデータ/{timestamp}_{user_id}.jpg"
    save_to_dropbox(image_data, dropbox_path)

    analyze_and_save(image_data, is_image=True)

    # 返信（固定）
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text="ありがとうございます")
    )

if __name__ == "__main__":
    app.run(debug=True)