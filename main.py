import os
from flask import Flask, request, abort
import openai
import dropbox
import requests
from linebot import LineBotApi
from linebot.models import TextSendMessage

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
GITHUB_COMMIT_AUTHOR = os.getenv("GITHUB_COMMIT_AUTHOR", "GPT PushBot <bot@example.com>")

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

        summary = gpt_summarize("新しいファイルの要約テストです。")
        notify_line(f"✅ GPT要約完了:\n{summary}")

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

# ✅ GitHub自動Push関数をここに定義（main.py内に埋め込み）
def push_to_github(filename, content, commit_message):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        # 既存ファイル確認（SHA取得のため）
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None

        payload = {
            "message": commit_message,
            "content": content.encode("utf-8").decode("utf-8").encode("base64").decode(),
            "branch": GITHUB_BRANCH,
            "committer": {
                "name": GITHUB_COMMIT_AUTHOR.split("<")[0].strip(),
                "email": GITHUB_COMMIT_AUTHOR.split("<")[1].replace(">", "").strip()
            }
        }
        if sha:
            payload["sha"] = sha

        res = requests.put(url, headers=headers, json=payload)
        return res.status_code, res.json()

    except Exception as e:
        print("GitHub Pushエラー:", e)
        return "error", str(e)

@app.route("/", methods=["GET"])
def home():
    return "📡 Yatagarasu GPT Auto System Running", 200

if __name__ == "__main__":
    app.run(debug=True)