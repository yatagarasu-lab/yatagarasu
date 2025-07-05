import os
import hashlib
import dropbox
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
import openai
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# 各種トークン取得
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask アプリとインスタンス
app = Flask(__name__)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# メモリで重複防止
hash_memory = set()

# トップページ確認
@app.route("/", methods=["GET"])
def home():
    return "LINE + Dropbox + GPT 連携動作中", 200

# Dropbox webhook（GET:検証用, POST:通知受取）
@app.route("/webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge"), 200
    elif request.method == "POST":
        print("✅ Dropbox webhook received.")
        process_latest_dropbox_file()
        return "", 200

# LINE メッセージ受信処理
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# LINEメッセージの返信
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text="ありがとうございます")
    )

# Dropbox ファイル処理
def process_latest_dropbox_file():
    folder_path = "/Apps/slot-data-analyzer"
    res = dbx.files_list_folder(folder_path)
    files = sorted(res.entries, key=lambda x: x.server_modified, reverse=True)

    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            path = file.path_display
            _, ext = os.path.splitext(path)
            if ext.lower() in [".txt", ".md", ".log"]:
                _, res = dbx.files_download(path)
                content = res.content.decode("utf-8")

                if is_duplicate(content):
                    print(f"⚠️ 重複ファイル検出（スキップ）: {path}")
                    return

                summary = ask_gpt(content)
                message = f"📄 {file.name} の要約:\n\n{summary}"
                push_line_message(message)
                return
    print("⚠️ 対象ファイルが見つかりません")

def is_duplicate(content):
    h = hashlib.sha256(content.encode()).hexdigest()
    if h in hash_memory:
        return True
    hash_memory.add(h)
    return False

def ask_gpt(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下の文章を要約してください。"},
                {"role": "user", "content": content}
            ],
            max_tokens=300
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        return f"要約: GPT解析エラー: {str(e)}"

def push_line_message(text):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextMessage(text=text))
        print("✅ LINEへ送信完了")
    except Exception as e:
        print("❌ LINE送信エラー:", str(e))

# 実行
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))