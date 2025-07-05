import os
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, ImageMessage
import dropbox
import openai
from datetime import datetime

# Flaskアプリ設定
app = Flask(__name__)

# 環境変数取得
CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TARGET_FOLDER_PATH = os.environ.get("TARGET_FOLDER_PATH", "/Apps/slot-data-analyzer")
LINE_USER_ID = os.environ.get("LINE_USER_ID")

# 各API初期化
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

# ファイル保存処理
def save_to_dropbox(file_content, filename):
    path = f"{TARGET_FOLDER_PATH}/{filename}"
    dbx.files_upload(file_content, path, mode=dropbox.files.WriteMode.overwrite)
    return path

# ファイルの重複チェック用ハッシュ生成
def file_hash(data):
    return hashlib.sha256(data).hexdigest()

# Dropbox内のファイルと重複判定
def is_duplicate(new_data):
    try:
        files = dbx.files_list_folder(TARGET_FOLDER_PATH).entries
        for f in files:
            if isinstance(f, dropbox.files.FileMetadata):
                _, res = dbx.files_download(f.path_display)
                if file_hash(res.content) == file_hash(new_data):
                    return True
    except Exception:
        pass
    return False

# GPT解析処理
def analyze_with_gpt(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下の内容がスロットかパチンコに関係する場合はA（スロット）、B（パチンコ）、それ以外はCとだけ返してください。"},
                {"role": "user", "content": content}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"解析失敗: {e}"

# LINEのWebhook受信
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# メッセージイベント処理
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    content = event.message.text.encode('utf-8')
    classification = analyze_with_gpt(content.decode("utf-8"))

    if classification == "A" or classification == "B":
        filename = f"text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        save_to_dropbox(content, filename)
        if event.source.user_id == LINE_USER_ID:
            line_bot_api.push_message(LINE_USER_ID, TextMessage(text="ありがとうございます"))
    else:
        # スロパチ以外 → 無視
        pass

# 画像イベント処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    image_data = message_content.content

    if is_duplicate(image_data):
        return  # 重複なら保存せず終了

    classification = analyze_with_gpt("これはスロットまたはパチンコの画像ですか？")

    if classification == "A" or classification == "B":
        filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        save_to_dropbox(image_data, filename)
        if event.source.user_id == LINE_USER_ID:
            line_bot_api.push_message(LINE_USER_ID, TextMessage(text="ありがとうございます"))

# 起動用
if __name__ == "__main__":
    app.run()