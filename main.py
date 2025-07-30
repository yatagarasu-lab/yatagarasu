import os
import hashlib
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
import dropbox
import requests
from openai import OpenAI
from google.generativeai import GenerativeModel, configure as configure_gemini

# --- Flask 初期化 ---
app = Flask(__name__)

# --- 環境変数から情報取得 ---
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_WATCH_FOLDER = os.getenv("DROPBOX_WATCH_FOLDER", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")
REPLY_TEXT = os.getenv("REPLY_TEXT", "ありがとうございます。処理が完了しました。")

# --- LINE 初期化 ---
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# --- Dropbox 初期化 ---
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

# --- Gemini 初期化（任意） ---
if GEMINI_API_KEY:
    configure_gemini(api_key=GEMINI_API_KEY)

# --- GPT 初期化 ---
openai = OpenAI(api_key=OPENAI_API_KEY)

# --- ファイルのハッシュ化（重複検出用） ---
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# --- ファイルをGPTで解析 ---
def analyze_with_gpt(content, filename="ファイル"):
    try:
        result = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{
                "role": "user",
                "content": f"{filename} の内容を要約・解析してください。\n\n{content[:4000]}"
            }],
            temperature=0.4
        )
        return result.choices[0].message.content
    except Exception as e:
        return f"[GPT解析エラー] {str(e)}"

# --- Gemini解析（オプション） ---
def analyze_with_gemini(content):
    try:
        model = GenerativeModel("gemini-pro")
        res = model.generate_content(content[:4000])
        return res.text
    except Exception as e:
        return f"[Gemini解析エラー] {str(e)}"

# --- LINE通知 ---
def notify_line(message):
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=message)
    )

# --- Webhook受信 ---
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    for entry in data.get("list_folder", {}).get("entries", []):
        if entry[0] == "file":
            path = entry[1]
            _, res = dbx.files_download(path)
            content = res.content.decode("utf-8", errors="ignore")

            gpt_summary = analyze_with_gpt(content, filename=path)
            gemini_summary = analyze_with_gemini(content) if GEMINI_API_KEY else None

            full_message = f"✅ GPT解析:\n{gpt_summary}"
            if gemini_summary:
                full_message += f"\n\n🔮 Gemini解析:\n{gemini_summary}"

            notify_line(full_message)

    return "OK"

# --- テスト用エンドポイント（起動確認用） ---
@app.route("/", methods=["GET"])
def index():
    return "🟢 GPT解析BOTは稼働中です！"

# --- アプリ起動 ---
if __name__ == "__main__":
    app.run()