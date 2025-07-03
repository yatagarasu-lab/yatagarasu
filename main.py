import os
import hashlib
import dropbox
import openai
from flask import Flask, request
from linebot import LineBotApi
from linebot.models import TextSendMessage
from datetime import datetime

app = Flask(__name__)

# 環境変数
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# 各API初期化
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

# Dropbox監視フォルダ
MONITOR_FOLDER = "/Apps/slot-data-analyzer"

# ファイルハッシュ取得（重複判定）
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# Dropboxファイル一覧
def list_files(folder_path):
    return dbx.files_list_folder(folder_path).entries

# ファイル読み込み
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# 重複削除機能
def find_duplicates(folder_path):
    files = list_files(folder_path)
    hash_map = {}
    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)
        if hash_value in hash_map:
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

# GPTの記録をDropboxに保存
def export_gpt_memory():
    now = datetime.now().strftime("%Y-%m-%d_%H%M")
    gpt_summary = (
        "【GPT記録】\n"
        "- 北斗：末尾3付近が高設定傾向あり。\n"
        "- グール：エピソードボーナス頻発は高設定示唆。\n"
        "- カスタム：朝カス・1000カス対応店舗の情報収集中。\n"
        "- 店舗傾向：5のつく日→ウエスタン葛西など強傾向。\n"
        "- 台番予測：直近は2000番台・3000番台に投入多し。\n"
    )
    filepath = f"{MONITOR_FOLDER}/GPT記録/gpt_{now}.txt"
    dbx.files_upload(gpt_summary.encode(), filepath, mode=dropbox.files.WriteMode("add"))
    return filepath

# LINE通知
def send_line_notify(msg):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=msg))
    except Exception as e:
        print("LINE通知エラー:", e)

# Webhook受信
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge", ""), 200
    elif request.method == "POST":
        print("Dropbox更新を検知")
        find_duplicates(MONITOR_FOLDER)
        export_path = export_gpt_memory()
        send_line_notify(f"🧠 GPT記録をDropboxに保存しました：\n{export_path}")
        return "", 200

# 動作確認用
@app.route("/")
def index():
    return "✅ GPT自動記録 & Dropbox連携中", 200