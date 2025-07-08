import os
import hashlib
import dropbox
import openai
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    TextMessage
)
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
    ImageMessageContent
)

# ----------------- 認証情報 -----------------
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# ----------------- 初期設定 -----------------
openai.api_key = OPENAI_API_KEY
app = Flask(__name__)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)

# Dropboxクライアント
try:
    dbx = dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )
except Exception as e:
    print("Dropbox認証エラー:", e)
    dbx = None

# ----------------- GPT解析 -----------------
def analyze_file_content(content: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下のスロット情報を要約・分析して、設定の傾向・注意点を簡潔に述べてください。"},
                {"role": "user", "content": content}
            ]
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"[GPT解析エラー] {str(e)}"

# ----------------- Dropbox 処理 -----------------
def file_hash(content):
    return hashlib.md5(content).hexdigest()

def is_duplicate(content):
    try:
        files = dbx.files_list_folder("/Apps/slot-data-analyzer").entries
        current_hash = file_hash(content)
        for f in files:
            if isinstance(f, dropbox.files.FileMetadata):
                _, res = dbx.files_download(f.path_display)
                if file_hash(res.content) == current_hash:
                    return True
        return False
    except Exception as e:
        print("重複チェック失敗:", str(e))
        return False

def save_file_to_dropbox(file_name, content):
    path = f"/Apps/slot-data-analyzer/{file_name}"
    dbx.files_upload(content, path, mode=dropbox.files.WriteMode.overwrite)
    return path

# ----------------- Webhookエンドポイント -----------------
@app.route("/", methods=["GET"])
def index():
    return "スロット解析BOTは稼働中です。Webhookは正常に待機中。"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return request.args.get("challenge", ""), 200

    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

# ----------------- LINE メッセージ処理 -----------------
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    reply_text = "ありがとうございます"
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(LINE_USER_ID, [TextMessage(text=reply_text)])

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    message_id = event.message.id
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        content_response = line_bot_api.get_message_content(message_id)
        binary = b"".join(content_response.iter_content(chunk_size=1024))

        if is_duplicate(binary):
            reply = "同じ画像はすでに保存済みです。"
        else:
            file_name = f"{message_id}.jpg"
            result_file = f"{message_id}_result.txt"

            # 保存
            save_file_to_dropbox(file_name, binary)

            # OCR + GPT解析
            import pytesseract
            from PIL import Image
            from io import BytesIO

            try:
                img = Image.open(BytesIO(binary))
                extracted_text = pytesseract.image_to_string(img, lang='jpn')
                analysis = analyze_file_content(extracted_text)
                save_file_to_dropbox(result_file, analysis.encode("utf-8"))
                reply = f"保存完了: {file_name}\n\n解析結果:\n{analysis[:500]}..."
            except Exception as e:
                reply = f"画像保存成功\n[解析エラー]: {str(e)}"

        line_bot_api.push_message(LINE_USER_ID, [TextMessage(text=reply)])

# ----------------- アプリ起動 -----------------
if __name__ == "__main__":
    app.run()