from flask import Flask, request
import os
import requests
import dropbox
import openai
from linebot import LineBotApi
from linebot.models import TextSendMessage
import hashlib

# --- 環境変数 ---
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
PARTNER_UPDATE_URL = os.getenv("PARTNER_UPDATE_URL")

# --- 初期化処理 ---
app = Flask(__name__)
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

# --- グローバル変数 ---
DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"
processed_hashes = set()

# --- ファイル一覧取得 ---
def list_files(path=DROPBOX_FOLDER_PATH):
    try:
        result = dbx.files_list_folder(path)
        return result.entries
    except Exception as e:
        print(f"[ファイル一覧取得エラー] {e}")
        return []

# --- ファイルダウンロード ---
def download_file(path):
    try:
        _, res = dbx.files_download(path)
        return res.content
    except Exception as e:
        print(f"[ファイルDLエラー] {e}")
        return None

# --- ハッシュ生成 ---
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# --- 要約生成 ---
def analyze_file_with_gpt(filename, content):
    prompt = f"以下を要約してください:\n\n{content.decode('utf-8', errors='ignore')}"
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT要約失敗] {e}"

# --- LINE 通知 ---
def send_line(text):
    try:
        msg = TextSendMessage(text=text)
        line_bot_api.push_message(LINE_USER_ID, messages=msg)
    except Exception as e:
        print(f"[LINE通知失敗] {e}")

# --- ファイル処理本体 ---
def process_new_files():
    files = list_files()
    for entry in files:
        fname = entry.name
        path = f"{DROPBOX_FOLDER_PATH}/{fname}"
        content = download_file(path)
        if not content:
            continue
        h = file_hash(content)
        if h in processed_hashes:
            print(f"重複 → {fname}")
            continue
        processed_hashes.add(h)
        summary = analyze_file_with_gpt(fname, content)
        send_line(f"【要約】{fname}\n{summary}")

# --- Dropbox Webhook受信 ---
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        if challenge:
            print("[Webhook認証] challenge を返します")
            return challenge, 200
        return "No challenge", 400

    if request.method == "POST":
        print("Webhook受信")
        process_new_files()
        if PARTNER_UPDATE_URL:
            try:
                requests.post(PARTNER_UPDATE_URL, timeout=3)
                print("相手に update-code 通知送信済")
            except Exception as e:
                print(f"[通知送信エラー] {e}")
        return "", 200

# --- update-code 受信エンドポイント ---
@app.route("/update-code", methods=["POST"])
def update_code():
    print("Updateコード受信")
    process_new_files()
    return "OK", 200

# --- ステータス確認用 ---
@app.route("/", methods=["GET"])
def home():
    files = list_files()
    return "<h2>八咫烏 BOT 起動中</h2><br>" + "<br>".join([f.name for f in files])

# --- 実行 ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)