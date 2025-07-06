from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, ImageMessage, TextSendMessage
import os
import openai
import dropbox
import hashlib
from io import BytesIO

# 初期化
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
dbx = dropbox.Dropbox(os.getenv("DROPBOX_ACCESS_TOKEN"))
openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# LINEユーザーID（固定で通知）
USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"

# ファイルの重複チェック用
def file_hash(content):
    return hashlib.md5(content).hexdigest()

hash_map = {}

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        events = handler.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, ImageMessage):
            # 画像の取得
            message_id = event.message.id
            message_content = line_bot_api.get_message_content(message_id)
            image_data = BytesIO(message_content.content)
            content = image_data.getvalue()

            # 重複チェック
            h = file_hash(content)
            if h in hash_map:
                print("重複ファイル。スキップします。")
                return "OK"
            hash_map[h] = True

            # ファイル名
            filename = f"/Apps/slot-data-analyzer/{message_id}.jpg"
            dbx.files_upload(content, filename)

            # 通知①：画像受信通知
            line_bot_api.push_message(USER_ID, TextSendMessage(text="画像を受け取りました。解析中です。"))

            # GPTで画像解析（OCRなどに変更可能）
            response = openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {"role": "system", "content": "この画像の内容を読み取り、スロットの設定推測に役立つ情報を要約してください。"},
                    {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"dropbox://{filename}"}}]},
                ],
                max_tokens=1000
            )

            result = response.choices[0].message.content

            # 通知②：解析完了メッセージ
            line_bot_api.push_message(USER_ID, TextSendMessage(text=f"解析が完了しました。ありがとうございます！\n\n📝解析結果:\n{result}"))

    return "OK"