import os
from flask import Flask, request, abort
import openai
import dropbox
import requests
import base64
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# ==== 環境変数の読み込み ====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # 例: "username/repo"
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_COMMIT_AUTHOR = os.getenv("GITHUB_COMMIT_AUTHOR", "GPT自動PushBot <bot@example.com>")

# ==== クライアント初期化 ====
openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# ==== DropboxリフレッシュトークンからAccessToken取得 ====
def get_dropbox_access_token():
    url = "https://api.dropboxapi.com/oauth2/token"
    headers = {
        "Authorization": "Basic " + base64.b64encode(f"{DROPBOX_CLIENT_ID}:{DROPBOX_CLIENT_SECRET}".encode()).decode(),
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json().get("access_token")

# ==== LINE通知 ====
def notify_line(message):
    try:
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=message)
        )
    except Exception as e:
        print("LINE通知エラー:", e)

# ==== ChatGPTによる要約 ====
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

# ==== GitHubにファイルPush ====
def push_to_github(filename, content, commit_message):
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # ファイルが存在するか確認
    get_resp = requests.get(url, headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

    payload = {
        "message": commit_message,
        "branch": GITHUB_BRANCH,
        "committer": {
            "name": GITHUB_COMMIT_AUTHOR.split(" <")[0],
            "email": GITHUB_COMMIT_AUTHOR.split("<")[1].rstrip(">")
        },
        "content": base64.b64encode(content.encode()).decode()
    }
    if sha:
        payload["sha"] = sha

    response = requests.put(url, headers=headers, json=payload)
    return response.status_code, response.json()

# ==== Webhookエンドポイント ====
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

        # ダミー要約処理（本来はDropboxからファイル取得）
        summary = gpt_summarize("新しいファイルの要約テストです。")
        notify_line(f"✅ GPT要約完了:\n{summary}")

        # GitHubへPush
        status, response = push_to_github(
            filename="auto_update.py",
            content="print('Hello from GPT!')",
            commit_message="自動更新：Dropbox経由で取得"
        )
        notify_line(f"📤 GitHub Push完了\nステータス: {status}")

        return "ok", 200

    except Exception as e:
        print("❌ Webhook処理エラー:", e)
        notify_line(f"❌ エラー:\n{e}")
        abort(500)

# ==== 動作確認用 ====
@app.route("/", methods=["GET"])
def home():
    return "📡 Yatagarasu GPT Auto System Running", 200

if __name__ == "__main__":
    app.run(debug=True)