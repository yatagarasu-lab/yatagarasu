import os
import requests
import base64
import json
from datetime import datetime
from flask import Flask, request, abort
import openai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# ==== Flask初期化 ====
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

# ==== API初期化 ====
openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ==== LINE通知 ====
def notify_line(message):
    try:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
    except Exception as e:
        print("LINE通知エラー:", e)

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

# ==== Dropbox アクセストークン取得 ====
def get_dropbox_access_token():
    try:
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
    except Exception as e:
        print("Dropboxトークン取得エラー:", e)
        return None

# ==== 最新ファイル取得 ====
def get_latest_dropbox_file():
    try:
        access_token = get_dropbox_access_token()
        if not access_token:
            return None

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        data = {"path": "/Apps/slot-data-analyzer", "recursive": False}
        resp = requests.post("https://api.dropboxapi.com/2/files/list_folder", headers=headers, json=data)
        resp.raise_for_status()
        files = [f for f in resp.json().get("entries", []) if f[".tag"] == "file"]
        if not files:
            return None
        return max(files, key=lambda x: x["client_modified"])["path_lower"]
    except Exception as e:
        print("Dropboxファイル取得エラー:", e)
        return None

# ==== ファイル内容ダウンロード ====
def download_dropbox_file_content(path):
    try:
        access_token = get_dropbox_access_token()
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Dropbox-API-Arg": json.dumps({"path": path})
        }
        resp = requests.post("https://content.dropboxapi.com/2/files/download", headers=headers)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print("Dropboxファイルダウンロードエラー:", e)
        return None

# ==== GitHubへPush ====
def push_to_github(filename, content, commit_message):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
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

# ==== LINE Webhook ====
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
    incoming_text = event.message.text.strip()

    if incoming_text == "要約開始":
        notify_line("🤖 要約トリガーを受信しました。処理を開始します…")
        try:
            from github_helper import is_duplicate_github_file
            from dropbox_handler import push_summary_to_github

            path = get_latest_dropbox_file()
            if not path:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ Dropboxにファイルが見つかりません。")
                )
                return

            content = download_dropbox_file_content(path)
            if not content:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="❌ Dropboxファイルの読み取りに失敗しました。")
                )
                return

            summary = gpt_summarize(content)
            today = datetime.now().strftime("%Y-%m-%d_%H-%M")
            github_filename = f"dropbox_summary_{today}.md"

            if is_duplicate_github_file(github_filename, summary):
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"⚠️ 同一ファイルが既にGitHubに存在します：{github_filename}")
                )
            else:
                status, result = push_to_github(
                    filename=github_filename,
                    content=summary,
                    commit_message="📄 Dropboxファイル要約を追加"
                )
                if status:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=f"✅ 要約をGitHubへ保存しました：{github_filename}")
                    )
                else:
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text=f"❌ GitHubへの保存に失敗しました：{result}")
                    )

            try:
                status2, _ = push_summary_to_github(summary)
                notify_line(f"📁 強化版GitHub保存完了: {status2}")
            except Exception as e:
                notify_line(f"⚠️ 強化版GitHub保存でエラー: {e}")

        except Exception as e:
            notify_line(f"❌ トリガー処理中にエラーが発生しました: {e}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"❌ エラーが発生しました：{e}")
            )
    else:
        reply_text = f"受信しました：{incoming_text}"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )

# ==== Dropbox Webhook ====
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge"), 200
    elif request.method == "POST":
        print("📦 Dropbox Webhook POST 受信（未使用）")
        return "OK", 200

# ==== 動作確認 ====
@app.route("/", methods=["GET"])
def home():
    return "📡 Yatagarasu GPT Auto System Running", 200

# ==== 実行 ====
if __name__ == "__main__":
    app.run()