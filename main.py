import os
from flask import Flask, request, abort
from dotenv import load_dotenv

# LINE関連
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# DropboxとGPT関連（services配下のモジュール）
from services.dropbox_handler import handle_dropbox_file_event
from services.gpt_summarizer import summarize_file

# 環境変数読み込み
load_dotenv()

# Flaskアプリ
app = Flask(__name__)

# LINE初期化
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

# Dropbox webhookエンドポイント
@app.route("/dropbox-webhook", methods=['GET', 'POST'])
def dropbox_webhook():
    if request.method == 'GET':
        return request.args.get('challenge')
    elif request.method == 'POST':
        print("✅ Dropbox Webhook POST受信")
        try:
            modified_files = handle_dropbox_file_event()
            print(f"📂 処理対象ファイル: {modified_files}")

            for file_path in modified_files:
                summary = summarize_file(file_path)
                print(f"🧠 要約結果: {summary}")

                if LINE_USER_ID:
                    line_bot_api.push_message(
                        LINE_USER_ID,
                        TextSendMessage(text=f"📝 要約:\n{summary}")
                    )

            return '', 200
        except Exception as e:
            print(f"❌ エラー: {e}")
            abort(500)

# LINE webhookエンドポイント
@app.route("/line-webhook", methods=['POST'])
def line_webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
            user_message = event.message.text
            reply_text = "ありがとうございます"
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_text)
            )

    return "OK"

# Renderのライブ確認用（任意）
@app.route("/", methods=["GET"])
def index():
    return "✅ Yatagarasu Auto System is Live"

# エントリーポイント
if __name__ == "__main__":
    app.run(debug=False)