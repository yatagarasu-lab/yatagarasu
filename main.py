import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import dropbox
import hashlib
import openai

load_dotenv()

app = Flask(__name__)

# LINE
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
USER_ID = os.getenv("LINE_USER_ID")

# Dropbox
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"

# OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# ファイルのハッシュ生成
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# Dropbox重複ファイルチェック
def is_duplicate_file(content):
    hash_value = file_hash(content)
    files = dbx.files_list_folder(DROPBOX_FOLDER_PATH).entries
    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            _, res = dbx.files_download(file.path_lower)
            if file_hash(res.content) == hash_value:
                return True
    return False

# ファイルアップロード
def upload_to_dropbox(file_name, content):
    path = f"{DROPBOX_FOLDER_PATH}/{file_name}"
    dbx.files_upload(content, path, mode=dropbox.files.WriteMode("overwrite"))

# OpenAIで解析
def analyze_file(filename, content):
    prompt = f"ファイル名: {filename}\nこのデータの要点をまとめてください。"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "あなたはスロットデータを解析するアシスタントです。"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message['content']

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
def handle_text_message(event):
    text = event.message.text
    line_bot_api.push_message(USER_ID, TextSendMessage(text="ありがとうございます"))

@handler.add(MessageEvent, message=TextMessage)
def handle_image(event):
    if isinstance(event.message, (TextMessage)):
        return

    message_content = line_bot_api.get_message_content(event.message.id)
    content = b"".join(chunk for chunk in message_content.iter_content())
    file_name = f"{event.message.id}.jpg"

    if is_duplicate_file(content):
        line_bot_api.push_message(USER_ID, TextSendMessage(text="重複ファイルのためスキップされました"))
        return

    upload_to_dropbox(file_name, content)
    result = analyze_file(file_name, content)
    line_bot_api.push_message(USER_ID, TextSendMessage(text=result))

# ポート番号をRender用に自動で取得
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Renderで自動セットされる想定
    app.run(host="0.0.0.0", port=port)