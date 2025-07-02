import os
from flask import Flask, request, abort
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import utils  # 先ほど作ったやつ
import openai

load_dotenv()

app = Flask(__name__)

# LINE
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/webhook", methods=['POST'])
def webhook():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()

    if user_message == "スロットデータ":
        files = utils.list_files_in_folder()
        if not files:
            reply = "Dropboxにファイルが見つかりませんでした。"
        else:
            latest_file = sorted(files)[-1]
            content = utils.download_file(f"/スロットデータ/{latest_file}")

            if content:
                prompt = f"以下のデータを解析し、スロットの設定や傾向を要約してください。\n\n{content.decode('utf-8')}"
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}]
                )
                reply = response.choices[0].message.content.strip()
            else:
                reply = "ファイルのダウンロードに失敗しました。"
    else:
        reply = "ありがとうございます"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )

if __name__ == "__main__":
    app.run()