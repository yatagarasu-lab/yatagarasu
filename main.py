from flask import Flask, request
import os
import requests
import dropbox
from openai import OpenAI            # ← v1 クライアント
from linebot import LineBotApi
from linebot.models import TextSendMessage
import hashlib
from threading import Thread
from github_utils import commit_text  # 使ってなければ残してOK

# --- 環境変数 ---
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY       = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET    = os.getenv("DROPBOX_APP_SECRET")
OPENAI_API_KEY        = os.getenv("OPENAI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID          = os.getenv("LINE_USER_ID")
PARTNER_UPDATE_URL    = os.getenv("PARTNER_UPDATE_URL")

# 解析結果のLINE通知 … デフォルトはオフ（"1"でオン）
NOTIFY_SUMMARY = os.getenv("NOTIFY_SUMMARY", "0") == "1"

# --- 初期化 ---
app = Flask(__name__)
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
oai = OpenAI(api_key=OPENAI_API_KEY)

# --- Health check（Render用） ---
@app.route("/healthz", methods=["GET"])
def healthz():
    return "ok", 200

# --- 定数 ---
DROPBOX_FOLDER_PATH = ""   # ルート監視（Dropboxは空文字が正）
processed_hashes = set()

# --- ファイル一覧取得（ページング対応） ---
def list_files(folder_path=DROPBOX_FOLDER_PATH):
    entries = []
    try:
        folder = "" if folder_path in ("", "/") else folder_path
        res = dbx.files_list_folder(folder)
        entries.extend(res.entries)
        while res.has_more:
            res = dbx.files_list_folder_continue(res.cursor)
            entries.extend(res.entries)
    except Exception as e:
        print(f"[ファイル一覧取得エラー] {e}")
    return entries

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
    return hashlib.sha256(content or b"").hexdigest()

# --- 要約処理（OpenAI v1 API） ---
def analyze_file_with_gpt(filename, content: bytes):
    text = content.decode("utf-8", errors="ignore")
    prompt = f"以下のテキストを簡潔に日本語で要約してください。\n\n{text}"
    try:
        resp = oai.chat.completions.create(
            model="gpt-4o-mini",        # コスト抑制。必要なら "gpt-4o"
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPT要約失敗] {e}"

# --- LINE通知（フラグで制御） ---
def send_line(text):
    if not NOTIFY_SUMMARY:
        return
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=text))
    except Exception as e:
        print(f"[LINE通知失敗] {e}")

# --- 新ファイル処理 ---
def process_new_files():
    files = list_files()
    for entry in files:
        fname = entry.name
        path = f"/{fname}" if DROPBOX_FOLDER_PATH in ("", "/") \
               else f"{DROPBOX_FOLDER_PATH.rstrip('/')}/{fname}"

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
            send_line(f"【要約】{fname}\n{summary}")
        except Exception as e:
            print(f"[ファイル処理失敗] {fname} | {e}")

# --- 非同期実行（Dropboxの10秒タイムアウト回避） ---
def _handle_async():
    try:
        process_new_files()
        if PARTNER_UPDATE_URL:
            try:
                requests.post(PARTNER_UPDATE_URL, timeout=3)
                print("相手にも update-code 通知送信済")
            except Exception as e:
                print(f"[通知送信エラー] {e}")
    except Exception as e:
        print(f"[非同期処理エラー] {e}")

# --- Dropbox Webhook ---
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        if challenge:
            print("[Webhook認証] challenge を返します")
            return challenge, 200
        return "No challenge", 400

    # POSTはすぐ200を返して裏で処理
    print("[Webhook POST受信] 非同期処理開始")
    Thread(target=_handle_async, daemon=True).start()
    return "", 200

# --- 外部からの更新トリガー ---
@app.route("/update-code", methods=["POST"])
def update_code():
    print("[Update-code 受信] 非同期処理開始")
    Thread(target=_handle_async, daemon=True).start()
    return "OK", 200

# --- ステータス表示 ---
@app.route("/", methods=["GET"])
def home():
    files = list_files()
    file_list = "<br>".join([f.name for f in files])
    return f"<h2>八咫烏 BOT 起動中</h2><p>{file_list}</p>"

# --- 起動 ---
if __name__ == "__main__":
    port = int(os.getenv("PORT", "10000"))   # Render/ローカル両対応
    app.run(host="0.0.0.0", port=port)