import os
import io
import hashlib
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage
from dotenv import load_dotenv
import dropbox
import openai
from PIL import Image
import pytesseract
from datetime import datetime

# 環境変数読み込み
load_dotenv()
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("USER_ID")

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Flaskアプリ定義（Render用）
app = Flask(__name__)

# LINE・OpenAI・Dropbox 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
openai.api_key = OPENAI_API_KEY
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# 画像要約バッファ
summary_buffer = []

# Webhook受信エンドポイント
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"エラー: {e}")
        abort(400)
    return "OK"

# 画像受信処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    try:
        message_id = event.message.id
        content = line_bot_api.get_message_content(message_id)
        image_data = io.BytesIO(content.content)
        image = Image.open(image_data)

        # OCR処理
        try:
            text = pytesseract.image_to_string(image, lang="jpn")
            if not text.strip():
                text = "（画像から文字を抽出できませんでした）"
        except Exception as e:
            text = f"（OCRエラー: {e}）"

        # GPTによる要約
        gpt_response = openai.ChatCompletion.create(
            model=GPT_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            messages=[
                {"role": "system", "content": "以下の日本語文章を簡潔に要約してください。"},
                {"role": "user", "content": text}
            ]
        )
        summary = gpt_response.choices[0].message["content"]

        # Dropbox保存
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}.jpg"
        path = f"/Apps/slot-data-analyzer/{filename}"
        image_data.seek(0)
        dbx.files_upload(image_data.read(), path)

        # バッファに保存
        summary_buffer.append(f"【{timestamp}】\n{summary.strip()}")

    except Exception as e:
        summary_buffer.append(f"解析失敗: {str(e)}")

# テキストメッセージ受信時の返信（バッファ送信）
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    try:
        if summary_buffer:
            full_summary = "\n\n".join(summary_buffer)
            line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=f"📝まとめ通知:\n\n{full_summary}"))
            summary_buffer.clear()
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ありがとうございます"))
    except Exception as e:
        print(f"通知エラー: {e}")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="通知に失敗しましたが、ありがとうございます"))

# アプリ起動（Render用）
if __name__ == "__main__":
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=debug_mode)