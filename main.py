from flask import Flask, request, abort
import os
import json
import dropbox
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from dropbox.oauth import DropboxOAuth2FlowNoRedirect
from dropbox.oauth import OAuth2Session

# Flaskアプリ初期化
app = Flask(__name__)

# LINE設定（環境変数から取得）
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")  # Push通知先のユーザーID
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox リフレッシュトークンでの初期化
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# Dropbox OAuth セッション生成
oauth_session = OAuth2Session(
    consumer_key=DROPBOX_APP_KEY,
    consumer_secret=DROPBOX_APP_SECRET,
    token={"refresh_token": DROPBOX_REFRESH_TOKEN},
    token_updater=lambda token: None
)
dbx = dropbox.Dropbox(oauth2_access_token=None, oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
                      app_key=DROPBOX_APP_KEY, app_secret=DROPBOX_APP_SECRET)

# Dropbox Webhookルート
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox webhook検証用（GET時はchallengeを返す）
        challenge = request.args.get("challenge")
        return challenge, 200

    if request.method == "POST":
        try:
            print("📩 Dropbox Webhook通知受信")
            payload = request.get_data(as_text=True)
            print("通知内容:", payload)
            line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text="📦 Dropboxにファイル変更がありました"))
            return '', 200
        except Exception as e:
            print(f"Webhookエラー: {e}")
            return 'Webhook Error', 500

# LINEのcallback（ユーザーからのメッセージ処理）
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    print("📥 LINEメッセージ受信:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# LINEからのメッセージに返信
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# アプリ起動
if __name__ == "__main__":
    app.run()