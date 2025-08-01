import os
import json
import dropbox
import openai
from flask import Flask, request, abort
from linebot import LineBotApi
from linebot.models import TextSendMessage

# 初期化
app = Flask(__name__)

# 環境変数読み込み
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 各APIクライアント
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

@app.route("/", methods=["GET"])
def index():
    return "Yatagarasu BOT is alive!"

@app.route("/dropbox_webhook", methods=["GET"])
def verify():
    return request.args.get("challenge")

@app.route("/dropbox_webhook", methods=["POST"])
def dropbox_webhook():
    data = request.get_json()
    print("Webhook received:", json.dumps(data))

    for account in data.get("list_folder", {}).get("accounts", []):
        process_dropbox_files()

    return "", 200

def process_dropbox_files():
    folder_path = "/Apps/slot-data-analyzer"
    entries = dbx.files_list_folder(folder_path).entries

    for entry in entries:
        if isinstance(entry, dropbox.files.FileMetadata):
            file_path = entry.path_lower
            _, res = dbx.files_download(file_path)
            content = res.content.decode("utf-8", errors="ignore")

            summary = ask_gpt(content)

            send_line_message(f"🧠 解析結果:\n\n{summary}")

def ask_gpt(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたはDropbox上のファイルを要約・分析するアシスタントです。"},
                {"role": "user", "content": text}
            ]
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[GPTエラー] {str(e)}"

def send_line_message(message):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
    except Exception as e:
        print("LINE送信エラー:", e)

if __name__ == "__main__":
    app.run()