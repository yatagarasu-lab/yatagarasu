import os
from flask import Flask, request, abort
import openai
import dropbox
from linebot import LineBotApi
from linebot.models import TextSendMessage
from github_push import push_to_github  # 別ファイルで定義

app = Flask(__name__)

# ==== 環境変数の読み込み ====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# GitHub Push 用
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_COMMIT_AUTHOR = os.getenv("GITHUB_COMMIT_AUTHOR")

# ==== クライアント初期化 ====
openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

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

        # 仮のGPT要約処理（ファイル未取得のテスト用）
        summary = gpt_summarize("新しいファイルの要約テストです。")
        notify_line(f"✅ GPT要約完了:\n{summary}")

        # GitHubにファイルPush（デモファイル）
        status, response = push_to_github(
            filename="auto_update.py",
            content="print('Hello from GPT!')",
            commit_message="自動更新：Dropbox経由で取得"
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