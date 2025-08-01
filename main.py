import os
import json
from flask import Flask, request, abort
import openai
import dropbox
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox.dropbox_client import Dropbox  # リフレッシュトークンで使える形式
from linebot import LineBotApi
from linebot.models import TextSendMessage
from github_push import push_to_github  # 別ファイルで定義

app = Flask(__name__)

# ==== 環境変数の読み込み ====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Dropboxのリフレッシュトークン方式
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# GitHub設定
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_COMMIT_AUTHOR = os.getenv("GITHUB_COMMIT_AUTHOR", "GPT PushBot <bot@example.com>")

# ==== 初期化 ====
openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Dropbox 初期化（リフレッシュトークン使用）
dbx = Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        body = request.json
        print("📦 Dropbox Webhook 受信:", body)

        entries = body.get("list_folder", {}).get("accounts", [])
        if not entries:
            print("⚠️ エントリなし")
            return "no change", 200

        notify_line("📥 Dropboxにファイルが追加されました。要約を開始します。")

        # 仮のGPT要約処理
        summary = gpt_summarize("新しいファイルの要約テストです。")
        notify_line(f"✅ GPT要約完了:\n{summary}")

        # GitHubにファイルPush
        status, response = push_to_github(
            filename="auto_update.py",
            content=f"print('GPT Summary: {summary}')",
            commit_message="自動更新：Dropboxファイル追加により要約"
        )
        notify_line(f"📤 GitHub自動Push完了\n結果: {status}")

        return "ok", 200

    except Exception as e:
        print("❌ エラー:", e)
        notify_line(f"❌ Webhook処理エラー:\n{e}")
        abort(500)


def gpt_summarize(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下の文章を簡潔に要約してください。"},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print("GPT要約エラー:", e)
        return "要約に失敗しました。"


def notify_line(message):
    try:
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=message)
        )
    except Exception as e:
        print("LINE通知エラー:", e)


@app.route("/", methods=["GET"])
def home():
    return "📡 Yatagarasu GPT Auto System Running", 200


if __name__ == "__main__":
    app.run(debug=True)