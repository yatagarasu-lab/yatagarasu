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
openai.api_key = os.getenv("OPENAI_API_KEY")

# ユーザー固定ID
USER_ID = "U8da89a1a4e1689bbf7077dbdf0d47521"

# 重複ファイル判定
def file_hash(content):
    return hashlib.md5(content).hexdigest()

hash_map = {}

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        events = handler.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, ImageMessage):
            message_id = event.message.id
            message_content = line_bot_api.get_message_content(message_id)
            image_data = BytesIO(message_content.content)
            content = image_data.getvalue()

            # 重複チェック
            h = file_hash(content)
            if h in hash_map:
                line_bot_api.push_message(USER_ID, TextSendMessage(text="同じ画像が既に解析済みのため、スキップしました。"))
                return "OK"
            hash_map[h] = True

            # Dropboxアップロード
            filename = f"/Apps/slot-data-analyzer/{message_id}_{h[:6]}.jpg"
            try:
                dbx.files_upload(content, filename)
            except Exception as e:
                print(f"Dropboxエラー: {e}")
                line_bot_api.push_message(USER_ID, TextSendMessage(text="Dropbox保存に失敗しました。"))
                return "OK"

            # LINE通知①
            line_bot_api.push_message(USER_ID, TextSendMessage(text="画像を受け取りました。解析中です。"))

            # GPT解析（Vision）
            try:
                response = openai.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {"role": "system", "content": "この画像の内容を読み取り、スロットの設定推測に役立つ情報を要約してください。"},
                        {"role": "user", "content": [{"type": "image_url", "image_url": {"url": f"dropbox://{filename}"}}]},
                    ],
                    max_tokens=1000
                )
                result = response.choices[0].message.content
            except Exception as e:
                result = "GPT解析中にエラーが発生しました。"

            # LINE通知②
            line_bot_api.push_message(USER_ID, TextSendMessage(text=f"解析が完了しました。ありがとうございます！\n\n📝解析結果:\n{result}"))

    return "OK"