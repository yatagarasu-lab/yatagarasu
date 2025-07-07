import os
import hashlib
import json
import tempfile
from flask import Flask, request
from dotenv import load_dotenv
from linebot import LineBotApi
from linebot.models import TextSendMessage
import dropbox
import pytesseract
from PIL import Image
import openai

# 初期化
load_dotenv()
app = Flask(__name__)

# 環境変数
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# インスタンス
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
openai.api_key = OPENAI_API_KEY

# 重複チェックマップ
file_hashes = {}

# ファイルのハッシュ計算
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# Dropboxからファイル一覧取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    res = dbx.files_list_folder(folder_path)
    return res.entries

# ファイルを一時保存＋OCR実行
def process_file(entry):
    path = entry.path_display
    _, ext = os.path.splitext(path)
    metadata, res = dbx.files_download(path)
    content = res.content
    hash_val = file_hash(content)

    # 重複ならスキップ
    if hash_val in file_hashes:
        return f"[重複スキップ] {path}"
    file_hashes[hash_val] = path

    # OCR処理
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    text = pytesseract.image_to_string(Image.open(tmp_path), lang='jpn')

    # GPT要約
    summary = summarize_with_gpt(text)
    return f"📄 {entry.name}\n📝 要約:\n{summary}"

# GPTによる要約
def summarize_with_gpt(text):
    try:
        if not text.strip():
            return "文字が検出されませんでした。"
        res = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下はスロットイベントやパチンコ店情報の画像から抽出された文字です。要点を簡潔にまとめてください。"},
                {"role": "user", "content": text}
            ],
            max_tokens=300,
        )
        return res['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"要約失敗: {e}"

# LINE通知
def send_line_notification(messages):
    full_message = "\n\n".join(messages)
    line_bot_api.push_message(
        LINE_USER_ID,
        TextSendMessage(text=full_message[:5000])  # LINE上限5000文字
    )

# Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        entries = list_files()
        messages = []
        for entry in entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                result = process_file(entry)
                if result:
                    messages.append(result)
        if messages:
            send_line_notification(messages)
        return "OK", 200
    except Exception as e:
        line_bot_api.push_message(
            LINE_USER_ID,
            TextSendMessage(text=f"❌ エラー: {e}")
        )
        return "Error", 500

if __name__ == "__main__":
    app.run()