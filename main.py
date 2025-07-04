import os
import hashlib
import dropbox
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage
from openai import OpenAI
import tempfile

app = Flask(__name__)

# 環境変数の読み込み
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")  # 固定返信対象

# 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai = OpenAI(api_key=OPENAI_API_KEY)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# Dropbox保存用関数
def save_to_dropbox(file_bytes, filename):
    path = f"/スロットデータ/{filename}"
    dbx.files_upload(file_bytes, path, mode=dropbox.files.WriteMode.overwrite)

# 受信と返信処理
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# メッセージ受信ハンドラー
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_text = event.message.text

    # GPTへ問い合わせ
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": user_text}],
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = f"エラーが発生しました: {e}"

    # Dropbox保存
    filename = f"text_{event.timestamp}.txt"
    save_to_dropbox(user_text.encode("utf-8"), filename)

    # LINE返信
    line_bot_api.push_message(USER_ID, TextSendMessage(text="ありがとうございます"))

# 画像メッセージ受信ハンドラー
@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)

    with tempfile.NamedTemporaryFile(delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tf.seek(0)
        image_bytes = tf.read()

    # Dropbox保存
    filename = f"image_{event.timestamp}.jpg"
    save_to_dropbox(image_bytes, filename)

    # GPTへ画像要約（省略可）

    # LINE返信
    line_bot_api.push_message(USER_ID, TextSendMessage(text="ありがとうございます"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)