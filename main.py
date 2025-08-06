from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError

import os
import dropbox
from openai import OpenAI

# Flaskアプリ初期化
app = Flask(__name__)

# 環境変数
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

# LINE API 初期化
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)


# ========================
# 🔁 Dropbox クライアント取得
# ========================
from dropbox.dropbox_client import Dropbox

def get_dropbox_client():
    return Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )


# ========================
# 💾 テキストをDropboxに保存
# ========================
def save_log_to_dropbox(filename: str, content: str):
    try:
        dbx = get_dropbox_client()
        path = f"/{filename}"
        dbx.files_upload(content.encode("utf-8"), path, mode=dropbox.files.WriteMode.overwrite)
        return f"✅ 保存完了: {filename}"
    except Exception as e:
        return f"❌ 保存失敗: {str(e)}"


# ========================
# 🔍 DropboxファイルをGPTで要約
# ========================
def analyze_dropbox_file_with_gpt(file_path: str):
    dbx = get_dropbox_client()
    _, res = dbx.files_download(file_path)
    file_content = res.content.decode("utf-8")

    client = OpenAI(api_key=OPENAI_API_KEY)
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "以下のファイル内容を要約してください。"},
            {"role": "user", "content": file_content}
        ]
    )

    return completion.choices[0].message.content


# ========================
# 🌐 LINE Webhookエンドポイント
# ========================
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# ========================
# 🌐 外部中継用エンドポイント（八咫烏などから転送される）
# ========================
@app.route("/receive", methods=["POST"])
def receive():
    payload = request.get_json(force=True)
    print("📦 受信した中継データ（八咫烏など）:", payload)
    return "✅ 受信完了", 200


# ========================
# 📩 メッセージイベント処理
# ========================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_msg = event.message.text.strip()

    # ✅ 保存コマンド（例：保存:log1.txt 内容:これはテスト）
    if user_msg.startswith("保存:") and "内容:" in user_msg:
        try:
            filename_part, content_part = user_msg.split("内容:", 1)
            filename = filename_part.replace("保存:", "").strip()
            content = content_part.strip()
            result = save_log_to_dropbox(filename, content)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))
        except Exception:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ コマンド形式エラー（保存:ファイル名 内容:内容）で送信してください）"))
        return

    # ✅ 解析コマンド（例：解析:/log1.txt）
    if user_msg.startswith("解析:"):
        try:
            path = user_msg.replace("解析:", "").strip()
            result = analyze_dropbox_file_with_gpt(path)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="🧠 GPT要約結果:\n" + result))
        except Exception as e:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 解析失敗:\n" + str(e)))
        return

    # それ以外の通常応答
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ ありがとうございます"))


# ========================
# 🚀 アプリ起動（Render用）
# ========================
if __name__ == "__main__":
    app.run()