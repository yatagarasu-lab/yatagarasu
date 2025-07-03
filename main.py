from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 自分のLINEチャネルアクセストークンとシークレットを入れる
line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    print("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Check your channel access token/secret.")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 👇ここでユーザーIDをログに出力
    print(f"User ID: {event.source.user_id}")
    
    # メッセージ内容もログ出力
    print(f"Message: {event.message.text}")
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text='ありがとうございます')
    )

if __name__ == "__main__":
    app.run()