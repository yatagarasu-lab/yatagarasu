import os
import tempfile
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
import dropbox
import datetime
from openai import OpenAI
from dotenv import load_dotenv
import hashlib

# 環境変数読み込み
load_dotenv()
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
USER_ID = os.getenv("LINE_USER_ID")

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
openai = OpenAI(api_key=OPENAI_API_KEY)

def categorize_content(text):
    if any(keyword in text.lower() for keyword in ['スロット', '差枚', '設定']):
        return "スロット"
    elif any(keyword in text.lower() for keyword in ['ロト', 'ミニロト', '宝くじ']):
        return "ミニロト"
    elif any(keyword in text.lower() for keyword in ['python', 'コード', 'プログラミング']):
        return "プログラミング"
    else:
        return "未分類"

def get_today_path(category, filename):
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    return f"/{today}/{category}/{filename}"

def save_to_dropbox(path, content):
    dbx.files_upload(content, f"/Apps/slot-data-analyzer{path}", mode=dropbox.files.WriteMode.overwrite)

def file_hash(content):
    return hashlib.md5(content).hexdigest()

hash_map = {}

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    if event.source.user_id != USER_ID:
        return
    text = event.message.text
    category = categorize_content(text)
    filename = f"text_{datetime.datetime.now().strftime('%H%M%S')}.txt"
    path = get_today_path(category, filename)
    save_to_dropbox(path, text.encode())
    print(f"[TEXT] 保存完了: {path}")
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    if event.source.user_id != USER_ID:
        return
    message_content = line_bot_api.get_message_content(event.message.id)
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        temp_path = tf.name

    with open(temp_path, "rb") as f:
        content = f.read()
        h = file_hash(content)
        if h in hash_map:
            print(f"[IMAGE] 重複ファイル検出 → スキップ")
            return
        else:
            hash_map[h] = True

        try:
            gpt_summary = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "画像の内容からカテゴリを判定して"},
                    {"role": "user", "content": "これは何に関する画像ですか？"}
                ]
            )
            category = categorize_content(gpt_summary.choices[0].message.content)
        except:
            category = "未分類"

        filename = f"img_{datetime.datetime.now().strftime('%H%M%S')}.jpg"
        path = get_today_path(category, filename)
        save_to_dropbox(path, content)
        print(f"[IMAGE] 保存完了: {path}")

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))

if __name__ == "__main__":
    app.run()