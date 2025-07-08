from flask import Flask, request, abort
import os
import hashlib
import dropbox
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

from openai import OpenAI
import time

app = Flask(__name__)

# --- 環境変数 ---
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- 初期化 ---
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
openai = OpenAI(api_key=OPENAI_API_KEY)

# --- 重複チェック用 ---
processed_hashes = {}

# --- ルート確認用 ---
@app.route("/", methods=['GET'])
def index():
    return "Bot is running"

# --- Dropbox Webhook 受信 ---
@app.route("/dropbox", methods=['POST'])
def dropbox_webhook():
    # Dropboxからの認証リクエストに対応
    if request.method == 'GET':
        return request.args.get('challenge')

    # POSTデータの処理開始
    dbx_path = "/Apps/slot-data-analyzer"
    try:
        entries = dbx.files_list_folder(dbx_path).entries
        for entry in entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                file_path = entry.path_display
                file_content = dbx.files_download(file_path)[1].content
                file_hash = hashlib.sha256(file_content).hexdigest()

                # 重複ファイルのスキップ
                if file_hash in processed_hashes:
                    continue
                processed_hashes[file_hash] = True

                # GPT解析
                result = analyze_with_gpt(file_content)

                # LINE通知
                push_to_line(f"🧠ファイル解析完了:\n{entry.name}\n\n📊結果:\n{result}")

        return "Processed", 200
    except Exception as e:
        push_to_line(f"❌Dropbox処理エラー:\n{str(e)}")
        return "Error", 500

# --- GPTによるファイル解析 ---
def analyze_with_gpt(content):
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下はDropboxから取得したデータです。内容を簡潔に要約し、重複やノイズがある場合は整理してください。"},
                {"role": "user", "content": content.decode("utf-8", errors="ignore")}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT解析失敗: {str(e)}"

# --- LINE Webhook受信（Reply対応） ---
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
def handle_message(event):
    if event.message.text.lower() in ["こんにちは", "解析して", "データ確認"]:
        reply_text = "ありがとうございます。データは受信次第、順次解析されます。"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# --- LINE Push通知関数 ---
def push_to_line(message):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
    except Exception as e:
        print(f"LINE通知失敗: {e}")

# --- アプリ起動 ---
if __name__ == "__main__":
    app.run()