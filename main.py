from flask import Flask, request, jsonify
import os
import dropbox
import hashlib
import base64
import openai
import requests

app = Flask(__name__)

# 環境変数取得
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.getenv("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.getenv("DROPBOX_CLIENT_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GAS_WEBHOOK_URL = os.getenv("GAS_WEBHOOK_URL")

openai.api_key = OPENAI_API_KEY

def get_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    payload = {
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "grant_type": "refresh_token",
        "client_id": DROPBOX_CLIENT_ID,
        "client_secret": DROPBOX_CLIENT_SECRET,
    }
    response = requests.post(url, data=payload)
    return response.json().get("access_token")

def list_files():
    dbx = dropbox.Dropbox(get_access_token())
    result = dbx.files_list_folder(path="/Apps/slot-data-analyzer", recursive=True)
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

def summarize_file(path):
    try:
        content = download_file(path)
        if path.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            base64_img = base64.b64encode(content).decode("utf-8")
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "user", "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}},
                        {"type": "text", "text": "この画像の内容を要約して下さい。"}
                    ]}
                ]
            )
            return response.choices[0].message.content
        else:
            text = content.decode("utf-8", errors="ignore")
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": f"以下を要約して下さい:\n{text}"}]
            )
            return response.choices[0].message.content
    except Exception as e:
        return f"要約エラー: {str(e)}"

def send_line_notify(message):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": message}]
    }
    res = requests.post(url, headers=headers, json=body)
    print(f"📬 LINE通知: {res.status_code} / {res.text}")

def send_to_spreadsheet(source, message):
    try:
        requests.post(GAS_WEBHOOK_URL, json={"source": source, "message": message})
    except Exception as e:
        print(f"❌ GAS送信エラー: {source} / {e}")

@app.route("/webhook", methods=["POST"])
def webhook():
    user_agent = request.headers.get("User-Agent", "").lower()
    if "line-bot" in user_agent:
        return handle_line_webhook()
    elif "dropbox" in user_agent:
        return handle_dropbox_webhook()
    return "Unknown source", 400

def handle_line_webhook():
    try:
        body = request.json
        print("✅ LINE Webhook受信: ", body)

        events = body.get("events", [])
        for event in events:
            if event["type"] == "message":
                reply_token = event["replyToken"]
                text = event["message"].get("text", "テキストがありません")
                reply_to_line(reply_token, f"ありがとうございます：{text}")
        return "OK", 200
    except Exception as e:
        print(f"❌ LINE処理エラー: {str(e)}")
        return "LINEエラー", 500

def reply_to_line(token, message):
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "replyToken": token,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post(url, headers=headers, json=payload)

def handle_dropbox_webhook():
    try:
        files = list_files()
        duplicates = find_duplicates(files)
        for file in files:
            if isinstance(file, dropbox.files.FileMetadata) and file.path_display not in duplicates:
                summary = summarize_file(file.path_display)
                name = os.path.basename(file.path_display)
                msg = f"📄: {name}\n📝: {summary}"
                send_line_notify(msg)
                send_to_spreadsheet(name, summary)
        if duplicates:
            dbx = dropbox.Dropbox(get_access_token())
            for d in duplicates:
                dbx.files_delete_v2(d)
        return jsonify({"status": "OK"}), 200
    except Exception as e:
        print(f"❌ Dropboxエラー: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "🟢 Yatagarasu Bot is Live"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)