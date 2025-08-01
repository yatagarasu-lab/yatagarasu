import os
import requests
import base64
from flask import Flask, request, abort
import openai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# ==== 環境変数 ====
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
GITHUB_COMMIT_AUTHOR = os.getenv("GITHUB_COMMIT_AUTHOR", "GPT Bot <bot@example.com>")

# ==== 初期化 ====
openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ==== Dropboxアクセストークン取得 ====
def get_dropbox_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET,
    }
    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# ==== GPT要約 ====
def gpt_summarize(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下の文章を要約してください。"},
                {"role": "user", "content": text}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        print("GPT要約エラー:", e)
        return "要約に失敗しました。"

# ==== LINE通知 ====
def notify_line(message):
    try:
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=message)
        )
    except Exception as e:
        print("LINE通知エラー:", e)

# ==== GitHubファイルPush ====
def push_to_github(filename, content, commit_message):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }

        # 既存SHA取得
        sha = None
        get_resp = requests.get(url, headers=headers)
        if get_resp.status_code == 200:
            sha = get_resp.json().get("sha")

        payload = {
            "message": commit_message,
            "content": base64.b64encode(content.encode()).decode(),
            "branch": GITHUB_BRANCH,
            "committer": {
                "name": GITHUB_COMMIT_AUTHOR.split("<")[0].strip(),
                "email": GITHUB_COMMIT_AUTHOR.split("<")[1].replace(">", "").strip()
            }
        }

        if sha:
            payload["sha"] = sha

        response = requests.put(url, headers=headers, json=payload)
        if response.status_code in (200, 201):
            return True, response.json()
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)

# ==== Dropbox Webhook認証エンドポイント ====
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return challenge, 200
    elif request.method == "POST":
        print("📦 Dropbox Webhook POST 受信（未使用エンドポイント）")
        return "OK", 200

# ==== Dropbox通知処理用エンドポイント ====
@app.route("/dropbox_webhook", methods=["POST"])
def dropbox_webhook():
    try:
        body = request.get_data(as_text=True)
        print("📦 Dropbox Webhook受信:", body)

        notify_line("📥 Dropboxにファイルが追加されました。要約を開始します。")
        summary = gpt_summarize("新しいファイルの要約テストです。")
        notify_line(f"✅ GPT要約完了:\n{summary}")

        status, response = push_to_github(
            filename="auto_update.py",
            content="print('Hello from GPT!')",
            commit_message="自動更新：Dropbox連携テスト"
        )
        notify_line(f"📤 GitHub自動Push完了\n結果: {status}")

        return "ok", 200
    except Exception as e:
        print("❌ Dropbox Webhook処理エラー:", e)
        notify_line(f"❌ Dropbox Webhook処理エラー:\n{e}")
        abort(500)

# ==== LINE BOT Webhook ====
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    incoming_text = event.message.text
    reply_text = f"受信しました：{incoming_text}"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# ==== Render動作確認 ====
@app.route("/", methods=["GET"])
def home():
    return "📡 Yatagarasu GPT Auto System Running", 200

if __name__ == "__main__":
    app.run()