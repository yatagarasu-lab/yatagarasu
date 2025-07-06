import os
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, ImageMessage, TextSendMessage
from openai import OpenAI
import dropbox

app = Flask(__name__)

# 環境変数の取得
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"  # ← 固定ユーザーID

# 各種APIクライアントの設定
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
client = OpenAI(api_key=OPENAI_API_KEY)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def save_to_dropbox(file_content, filename):
    dropbox_path = f"/Apps/slot-data-analyzer/{filename}"
    dbx.files_upload(file_content, dropbox_path, mode=dropbox.files.WriteMode("overwrite"))
    return dropbox_path

def analyze_with_gpt(image_bytes):
    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {"role": "user", "content": [
                {"type": "text", "text": "以下の画像を解析して結果を要約してください。"},
                {"type": "image_url", "image_url": {
                    "url": "data:image/jpeg;base64," + image_bytes.decode("utf-8")}}
            ]}
        ],
        max_tokens=1000
    )
    return response.choices[0].message.content

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    signature = request.headers["X-Line-Signature"]

    try:
        events = handler.parser.parse(body, signature)
    except Exception as e:
        print(f"Signature validation failed: {e}")
        abort(400)

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, ImageMessage):
            # 一時ファイルとして保存
            message_id = event.message.id
            message_content = line_bot_api.get_message_content(message_id)

            image_data = b""
            for chunk in message_content.iter_content():
                image_data += chunk

            filename = f"{message_id}.jpg"
            save_to_dropbox(image_data, filename)

            # ① 受信直後に通知
            line_bot_api.push_message(
                USER_ID,
                TextSendMessage(text="画像を受け取りました。解析中です。")
            )

            # ② GPTで解析
            import base64
            encoded = base64.b64encode(image_data)
            try:
                result = analyze_with_gpt(encoded)
            except Exception as e:
                result = f"解析中にエラーが発生しました: {e}"

            # ③ 結果を通知
            line_bot_api.push_message(
                USER_ID,
                TextSendMessage(text="解析が完了しました。ありがとうございます！\n\n" + result)
            )

    return "OK", 200