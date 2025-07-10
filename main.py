import os
import json
import hashlib
import dropbox
from flask import Flask, request
from datetime import datetime
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage

# 環境変数からトークンを取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")  # 固定返信先

# 各種インスタンス
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

app = Flask(__name__)

# ファイルの重複チェック用ハッシュ
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# Dropboxのフォルダからファイル一覧を取得
def list_files(folder_path="/Apps/slot-data-analyzer"):
    return dbx.files_list_folder(folder_path).entries

# Dropboxからファイルをダウンロード
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# GPTログをDropboxに保存
def save_gpt_log(user_id, prediction, result, category="slot"):
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "category": category,
        "prediction": prediction,
        "result": result
    }
    filename = f"/gpt_logs/{category}_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    content = json.dumps(log_entry, ensure_ascii=False, indent=2)
    dbx.files_upload(content.encode(), filename, mode=dropbox.files.WriteMode("add"))

# ファイルの重複をチェック・削除
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)
        if hash_value in hash_map:
            dbx.files_delete_v2(path)
        else:
            hash_map[hash_value] = path

# Webhookのエンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, request.headers['X-Line-Signature'])
    except Exception as e:
        print(f"Error: {e}")
    return 'OK'

# ユーザーからのメッセージ処理
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()
    
    # GPT記録コマンド例: 「予想 保存」
    if text.startswith("予想"):
        prediction = "北斗102番台 / グール121番台"
        result = "北斗 +3200枚 / グール -150枚"
        save_gpt_log(event.source.user_id, prediction, result)
        reply = "予想と結果を記録しました。"
    else:
        reply = "ありがとうございます"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# 起動コマンド
if __name__ == "__main__":
    app.run()