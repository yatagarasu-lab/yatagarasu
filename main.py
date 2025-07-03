import os
import hashlib
import dropbox
import openai
from flask import Flask, request, jsonify
from linebot import LineBotApi
from linebot.models import TextSendMessage
from datetime import datetime

app = Flask(__name__)

# 環境変数
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 各サービス初期化
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

# Dropbox監視フォルダ
MONITOR_FOLDER = "/Apps/slot-data-analyzer"

# ファイルのハッシュ生成
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# Dropboxからファイル一覧を取得
def list_files(folder_path):
    return dbx.files_list_folder(folder_path).entries

# ファイルの重複チェック
def find_duplicates(folder_path):
    files = list_files(folder_path)
    hash_map = {}
    for file in files:
        path = file.path_display
        _, res = dbx.files_download(path)
        content = res.content
        hash_val = file_hash(content)
        if hash_val in hash_map:
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_val] = path

# GPTで内容要約
def summarize_content(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "次の内容を要約してください。"},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.strip()

# GPT記録内容をDropboxに自動エクスポート
def export_gpt_memory():
    now = datetime.now().strftime("%Y-%m-%d_%H%M")
    summary_text = "【GPT記録エクスポート】\n- 分析内容、傾向、予測などをここに記述（例：今後の東京グール設定傾向）"
    filename = f"/Apps/slot-data-analyzer/gpt_summary_{now}.txt"
    dbx.files_upload(summary_text.encode(), filename, mode=dropbox.files.WriteMode("add"))
    return filename

# LINE通知
def send_line_notify(text):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
    except Exception as e:
        print("LINE通知エラー:", e)

# Webhook確認用（Dropbox）
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return challenge, 200
    elif request.method == "POST":
        print("DropboxからWebhook通知受信")
        find_duplicates(MONITOR_FOLDER)
        export_path = export_gpt_memory()
        send_line_notify(f"📦 新しいデータとGPT記録を保存しました：\n{export_path}")
        return "", 200

# 動作確認用エンドポイント
@app.route("/")
def index():
    return "GPT + Dropbox + LINE Bot: running OK", 200