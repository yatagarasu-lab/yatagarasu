from flask import Flask, request, abort
import os
import json
import traceback
import dropbox
import io
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# ===== LINE設定 =====
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID", "U8da89a1a4e1689bbf7077dbdf0d47521")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ===== Dropbox設定（リフレッシュトークン方式でもOK）=====
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# ===== ファイルOCR解析 =====
def analyze_file(file_path):
    try:
        _, ext = os.path.splitext(file_path.lower())
        metadata, res = dbx.files_download(file_path)
        file_data = res.content

        # PDFの場合
        if ext == ".pdf":
            text = ""
            with fitz.open(stream=file_data, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text()
            return text.strip()

        # 画像（JPEG/PNGなど）
        elif ext in [".jpg", ".jpeg", ".png"]:
            img = Image.open(io.BytesIO(file_data))
            text = pytesseract.image_to_string(img, lang="jpn+eng")
            return text.strip()

        else:
            return f"未対応ファイル形式: {ext}"

    except Exception as e:
        print("❌ 解析エラー:", str(e))
        return f"[解析エラー]: {str(e)}"

# ===== Webhookエンドポイント =====
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        challenge = request.args.get("challenge", "")
        return str(challenge), 200

    if request.method == "POST":
        try:
            data = request.get_json(silent=True)
            print("📩 Dropbox Webhook通知を受信")

            for entry in data.get("list_folder", {}).get("entries", []):
                if isinstance(entry, list) and len(entry) >= 2:
                    path = entry[1].get("path_display")
                    print("🔍 処理ファイル:", path)

                    # ファイル内容取得・解析
                    result_text = analyze_file(path)

                    # LINE通知
                    line_bot_api.push_message(
                        LINE_USER_ID,
                        TextSendMessage(text=f"📄 {path} の内容を解析しました：\n\n{result_text[:1000]}")
                    )

            return "", 200
        except Exception as e:
            print("❌ Webhookエラー:", str(e))
            traceback.print_exc()

            try:
                line_bot_api.push_message(
                    LINE_USER_ID,
                    TextSendMessage(text=f"[Webhookエラー]\n{str(e)}")
                )
            except:
                pass

            return "Internal Server Error", 500

# ===== LINE Callbackエンドポイント =====
@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    print("💬 LINE Message:", body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

# ===== LINE受信メッセージ応答 =====
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    reply_text = "ありがとうございます"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

# ===== アプリ起動 =====
if __name__ == "__main__":
    app.run()