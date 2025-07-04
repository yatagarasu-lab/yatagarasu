import os
import hashlib
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dotenv import load_dotenv
import dropbox
import openai

# 環境変数の読み込み
load_dotenv()

# Flask アプリ
app = Flask(__name__)

# LINE API 初期化
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox 初期化
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# OpenAI APIキー
openai.api_key = os.getenv("OPENAI_API_KEY")

# ファイルのハッシュ値を生成（重複判定用）
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# Dropboxファイル一覧取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

# ファイルをダウンロード
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content.decode("utf-8", errors="ignore")

# GPTで要約・重複チェック処理
def analyze_and_deduplicate(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    report = []

    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            dbx.files_delete_v2(path)
            report.append(f"❌ 重複削除: {os.path.basename(path)}")
        else:
            hash_map[hash_value] = path
            try:
                gpt_response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "これはDropboxに保存されたスロットに関する情報です。内容を要約し、重要なポイントを抽出してください。"},
                        {"role": "user", "content": content}
                    ]
                )
                summary = gpt_response['choices'][0]['message']['content']
                report.append(f"✅ {os.path.basename(path)}\n{summary}")
            except Exception as e:
                report.append(f"⚠️ {os.path.basename(path)}: GPT解析失敗 ({e})")

    return "\n\n".join(report)

# LINE通知送信
def send_line_message(text):
    line_bot_api.push_message(USER_ID, TextSendMessage(text=text))

# Webhookエンドポイント
@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# ユーザーがLINEに送ったメッセージ処理（任意）
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip().lower()
    if text == "解析":
        result = analyze_and_deduplicate()
        send_line_message(f"📊 最新解析結果:\n\n{result}")
    else:
        send_line_message("ありがとうございます")

# Dropbox webhookトリガー（ファイル追加時用）
@app.route("/dropbox_webhook", methods=["POST"])
def dropbox_webhook():
    result = analyze_and_deduplicate()
    send_line_message(f"📥 Dropboxに新ファイル\n\n{result}")
    return "OK", 200

# webhook検証GET
@app.route("/dropbox_webhook", methods=["GET"])
def dropbox_verify():
    challenge = request.args.get("challenge")
    return challenge, 200

# Render用
@app.route("/")
def index():
    return "Slot Data Analyzer is running."

if __name__ == "__main__":
    app.run()