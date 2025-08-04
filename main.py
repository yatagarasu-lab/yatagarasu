from flask import Flask, request, jsonify
import os
import dropbox
import hashlib
from io import BytesIO
from PIL import Image
import base64
import openai
import requests

# LINE SDK
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

# 環境変数の読み込み
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GAS_WEBHOOK_URL = os.getenv("GAS_WEBHOOK_URL")

openai.api_key = OPENAI_API_KEY
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox アクセストークン取得
def get_access_token():
    token_url = "https://api.dropbox.com/oauth2/token"
    payload = {
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "grant_type": "refresh_token",
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET,
    }
    response = requests.post(token_url, data=payload)
    return response.json().get("access_token")

# Dropbox ファイル操作
def list_files():
    dbx = dropbox.Dropbox(get_access_token())
    result = dbx.files_list_folder(path="", recursive=True)
    return result.entries

def download_file(path):
    dbx = dropbox.Dropbox(get_access_token())
    metadata, res = dbx.files_download(path)
    return res.content

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def find_duplicates(files):
    hash_map = {}
    duplicates = []
    for file in files:
        if isinstance(file, dropbox.files.FileMetadata):
            content = download_file(file.path_display)
            hash_val = file_hash(content)
            if hash_val in hash_map:
                duplicates.append(file.path_display)
            else:
                hash_map[hash_val] = file.path_display
    return duplicates

# GPTによる要約
def summarize_file(file_path):
    try:
        content = download_file(file_path)
        if file_path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            base64_img = base64.b64encode(content).decode("utf-8")
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}},
                        {"type": "text", "text": "この画像を要約してください。"}
                    ]}
                ]
            )
            return response.choices[0].message.content
        elif file_path.lower().endswith((".txt", ".csv", ".log", ".json")):
            text = content.decode("utf-8", errors="ignore")
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": f"以下を要約してください:\n{text}"}
                ]
            )
            return response.choices[0].message.content
        else:
            return "対応していないファイル形式です。"
    except Exception as e:
        return f"要約失敗: {str(e)}"

# LINE通知
def send_line_notify(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    res = requests.post(url, headers=headers, json=payload)
    print(f"📬 LINE通知: {res.status_code} / {res.text}")

# GAS送信
def send_to_spreadsheet(source, message):
    payload = {
        "source": source,
        "message": message
    }
    try:
        response = requests.post(GAS_WEBHOOK_URL, json=payload)
        print(f"📤 GAS送信結果: {response.status_code} / {response.text}")
    except Exception as e:
        print(f"❌ GAS送信エラー: {source} / {e}")

# Webhook統合ルート
@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Dropbox challenge対応
        challenge = request.args.get("challenge")
        if challenge:
            print(f"✅ Dropbox challenge応答: {challenge}")
            return challenge, 200

    user_agent = request.headers.get("User-Agent", "").lower()
    print(f"📩 Webhook受信: User-Agent={user_agent}")

    if "line-bot" in user_agent:
        return handle_line_webhook()
    elif "dropbox" in user_agent:
        return handle_dropbox_webhook()
    else:
        print("⚠️ 未知のWebhookリクエスト")
        return "Unknown webhook source", 400

# Dropbox Webhook処理
def handle_dropbox_webhook():
    try:
        files = list_files()
        duplicates = find_duplicates(files)

        for file in files:
            if isinstance(file, dropbox.files.FileMetadata) and file.path_display not in duplicates:
                summary = summarize_file(file.path_display)
                file_name = os.path.basename(file.path_display)
                message = f"📄ファイル: {file_name}\n📝要約: {summary}"
                send_line_notify(message)
                send_to_spreadsheet(file_name, summary)

        if duplicates:
            dbx = dropbox.Dropbox(get_access_token())
            for dup in duplicates:
                dbx.files_delete_v2(dup)
                print(f"🗑️ 重複削除: {dup}")

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"❌ Dropbox処理エラー: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# LINE Webhook処理
def handle_line_webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
        print("✅ LINE Webhook処理成功")
        return "LINE webhook OK", 200
    except InvalidSignatureError:
        print("❌ LINE署名エラー")
        return "Invalid signature", 400

@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    text = event.message.text
    print(f"📝 LINEテキスト受信: {text}")
    send_to_spreadsheet("LINE Text", text)
    send_line_notify(f"🗒️ 受信テキスト: {text}")

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_id = event.message.id
    message_content = line_bot_api.get_message_content(message_id)

    img_path = f"/tmp/{message_id}.jpg"
    with open(img_path, "wb") as f:
        for chunk in message_content.iter_content():
            f.write(chunk)

    with open(img_path, "rb") as f:
        content = f.read()

    base64_img = base64.b64encode(content).decode("utf-8")
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}},
                    {"type": "text", "text": "この画像の内容を要約してください。"}
                ]}
            ]
        )
        summary = response.choices[0].message.content
        send_line_notify(f"🖼️ 画像要約: {summary}")
        send_to_spreadsheet("LINE Image", summary)
    except Exception as e:
        print(f"❌ LINE画像処理エラー: {e}")

@app.route("/", methods=["GET"])
def index():
    return "📡 Yatagarasu GPT Automation is running."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)