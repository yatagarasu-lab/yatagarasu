from flask import Flask, request
import os
import requests
import dropbox
import openai
from linebot import LineBotApi
from linebot.models import TextSendMessage
import hashlib
from github_utils import commit_text  # 🔹GitHubユーティリティ

# --- 環境変数 ---
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
PARTNER_UPDATE_URL = os.getenv("PARTNER_UPDATE_URL")

# --- 初期化 ---
app = Flask(__name__)
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY

# --- GitHub への手動ハートビート用エンドポイント ---
@app.route("/push-github", methods=["POST"])
def push_github():
    try:
        summary = "Auto update: service heartbeat and last-run OK\n"
        msg = commit_text(
            repo_path="ops/last_run.log",
            text=summary,
            commit_message="chore: auto heartbeat push"
        )
        return msg, 200
    except Exception as e:
        return f"❌ GitHub push failed: {e}", 500

# --- 定数 ---
DROPBOX_FOLDER_PATH = ""  # ルート監視（フルDropbox想定）
processed_hashes = set()

# --- ファイル一覧取得 ---
def list_files(folder_path=DROPBOX_FOLDER_PATH):
    try:
        # ルートは空文字を要求するDropbox API仕様に合わせる
        folder = folder_path if folder_path != "/" else ""
        result = dbx.files_list_folder(folder)
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

# --- ハッシュ作成 ---
def file_hash(content):
    if content is None:
        return ""
    return hashlib.sha256(content).hexdigest()

# --- 要約処理 ---
def analyze_file_with_gpt(filename, content):
    prompt = f"以下を要約してください:\n\n{content.decode('utf-8', errors='ignore')}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT要約失敗] {e}"

# --- LINE通知 ---
def send_line(text):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
    except Exception as e:
        print(f"[LINE通知失敗] {e}")

# --- 新ファイル処理 ---
def process_new_files():
    files = list_files()
    for entry in files:
        fname = entry.name
        # ルート監視時も必ず "/filename" にする
        if DROPBOX_FOLDER_PATH in ("", "/"):
            path = f"/{fname}"
        else:
            path = f"{DROPBOX_FOLDER_PATH.rstrip('/')}/{fname}"

        content = download_file(path)
        if not content:
            continue

        h = file_hash(content)
        if h in processed_hashes:
            print(f"重複 → {fname}")
            continue

        processed_hashes.add(h)
        try:
            summary = analyze_file_with_gpt(fname, content)
            # ※今は通知する仕様のまま。不要ならここをコメントアウト
            send_line(f"【要約】{fname}\n{summary}")
        except Exception as e:
            print(f"[ファイル処理失敗] {fname} | {e}")

# --- Dropbox Webhook ---
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        if challenge:
            print("[Webhook認証] challenge を返します")
            return challenge, 200
        return "No challenge", 400

    if request.method == "POST":
        print("[Webhook POST受信]")
        process_new_files()
        if PARTNER_UPDATE_URL:
            try:
                requests.post(PARTNER_UPDATE_URL, timeout=3)
                print("相手にも update-code 通知送信済")
            except Exception as e:
                print(f"[通知送信エラー] {e}")
        return "", 200

# --- 外部からの更新トリガー ---
@app.route("/update-code", methods=["POST"])
def update_code():
    print("[Update-code 受信]")
    process_new_files()
    return "OK", 200

# --- ステータス表示 ---
@app.route("/", methods=["GET"])
def home():
    files = list_files()
    file_list = "<br>".join([f.name for f in files])
    return f"<h2>八咫烏 BOT 起動中</h2><p>{file_list}</p>"

# --- 起動 ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)