from flask import Blueprint, request, jsonify
import dropbox
import hashlib
import os
from utils.logger import log_event

webhook_bp = Blueprint("webhook_bp", __name__)

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
GPT_API_KEY = os.getenv("OPENAI_API_KEY")

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# 重複チェック用ハッシュ保存
hash_cache = set()

def calculate_hash(file_content):
    return hashlib.md5(file_content).hexdigest()

def send_line_message(text):
    import requests
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    body = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text}]
    }
    response = requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=body)
    return response.status_code

def analyze_with_gpt(file_content):
    import openai
    openai.api_key = GPT_API_KEY

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "これはDropboxにアップロードされたファイルの内容です。要約・分類・解析を実行してください。"},
                {"role": "user", "content": file_content.decode("utf-8", errors="ignore")[:8000]}
            ]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"GPT解析中にエラー発生: {e}"

@webhook_bp.route("/webhook", methods=["GET"])
def verify_webhook():
    challenge = request.args.get("challenge")
    return challenge, 200

@webhook_bp.route("/webhook", methods=["POST"])
def process_dropbox_event():
    data = request.get_json()
    log_event(f"📥 Dropbox Webhook Received:\n{data}")

    for entry in data.get("list_folder", {}).get("entries", []):
        if entry[0] != "file":
            continue

        file_path = entry[1].get("path_display")
        log_event(f"📄 新ファイル検出: {file_path}")

        try:
            metadata, res = dbx.files_download(file_path)
            content = res.content
            file_hash = calculate_hash(content)

            if file_hash in hash_cache:
                log_event(f"⚠️ 重複ファイル: {file_path}")
                return "Duplicate", 200
            hash_cache.add(file_hash)

            # GPTで解析
            analysis_result = analyze_with_gpt(content)
            log_event(f"🔍 GPT解析結果:\n{analysis_result}")

            # LINE通知
            send_line_message(f"📎ファイル解析完了\n{file_path}\n\n{analysis_result[:1000]}")

        except Exception as e:
            log_event(f"❌ 処理エラー: {e}")
            send_line_message(f"エラー発生: {e}")
            return "Error", 500

    return "OK", 200