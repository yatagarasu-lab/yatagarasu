from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# 環境変数からLINEのトークンとシークレットを取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")

# Botインスタンス作成
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Webhookの受け口
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')

    # リクエストボディ取得
    body = request.get_data(as_text=True)

    # 検証（失敗したら400エラー）
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# テキストメッセージを受信したときの処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply_text = "ありがとうございます"
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# ローカル動作用（Renderでは不要だが記述しておいてOK）
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)