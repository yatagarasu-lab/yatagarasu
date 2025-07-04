from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import os
import dropbox
import hashlib
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# LINE設定
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Dropbox設定
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

# ユーザーID（Push通知用）
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Flaskアプリ
app = Flask(__name__)

# OpenAI設定
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ファイルのハッシュ計算
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# Dropboxへ保存
def save_to_dropbox(file_path, content):
    dbx.files_upload(content, file_path, mode=dropbox.files.WriteMode.overwrite)

# Dropbox内のファイル一覧取得
def list_files(folder_path):
    result = dbx.files_list_folder(folder_path)
    return result.entries

# Dropboxからファイルをダウンロード
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# 重複判定
def is_duplicate(new_content):
    new_hash = file_hash(new_content)
    for file in list_files(DROPBOX_FOLDER):
        existing = download_file(file.path_display)
        if file_hash(existing) == new_hash:
            return True, file.name
    return False, None

# GPTによる要約
def analyze_file(content):
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "画像またはテキストの内容をスロットイベントデータとして要約してください"},
            {"role": "user", "content": content.decode("utf-8", errors="ignore")}
        ]
    )
    return response.choices[0].message.content.strip()

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# テキストメッセージ処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text.encode("utf-8")
    file_path = f"{DROPBOX_FOLDER}/{event.timestamp}.txt"

    duplicate, existing = is_duplicate(text)
    if not duplicate:
        save_to_dropbox(file_path, text)
        summary = analyze_file(text)

        # LINE通知
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"""
📦 テキスト保存完了！
- ファイル名: {event.timestamp}.txt
- 重複: ❌なし
- 要約: {summary}
"""))
    else:
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"""
⚠️ 重複ファイルを検出しました
- 元ファイル名: {existing}
- 処理をスキップしました
"""))

# 画像メッセージ処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = b"".join(chunk for chunk in message_content.iter_content())
    file_path = f"{DROPBOX_FOLDER}/{event.timestamp}.jpg"

    duplicate, existing = is_duplicate(image_data)
    if not duplicate:
        save_to_dropbox(file_path, image_data)
        summary = analyze_file(image_data)

        # LINE通知
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"""
🖼️ 画像保存完了！
- ファイル名: {event.timestamp}.jpg
- 重複: ❌なし
- 要約: {summary}
"""))
    else:
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=f"""
⚠️ 重複画像を検出しました
- 元ファイル名: {existing}
- 処理をスキップしました
"""))

# アプリ起動
if __name__ == "__main__":
    app.run()