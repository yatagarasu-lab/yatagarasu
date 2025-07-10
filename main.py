import os
import json
import hashlib
import dropbox
from flask import Flask, request
from datetime import datetime
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 環境変数の取得
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")  # 通知先固定ユーザーID

# 初期化
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
app = Flask(__name__)

# ファイルのハッシュ計算
def file_hash(content):
    return hashlib.md5(content).hexdigest()

# Dropboxフォルダのファイル一覧
def list_files(folder_path="/Apps/slot-data-analyzer"):
    try:
        return dbx.files_list_folder(folder_path).entries
    except dropbox.exceptions.ApiError:
        return []

# ファイル内容の取得
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content

# 重複ファイル削除
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}
    for file in files:
        path = file.path_display
        content = download_file(path)
        h = file_hash(content)
        if h in hash_map:
            dbx.files_delete_v2(path)
        else:
            hash_map[h] = path

# GPTログを保存
def save_gpt_log(user_id, prediction, result, category="slot"):
    log = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "category": category,
        "prediction": prediction,
        "result": result
    }
    folder = "/Apps/slot-data-analyzer/gpt_logs"
    filename = f"{folder}/{category}_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    dbx.files_upload(json.dumps(log, ensure_ascii=False, indent=2).encode(), filename)

# Webhook受信
@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    signature = request.headers['X-Line-Signature']
    try:
        handler.handle(body, signature)
    except Exception as e:
        print(f"エラー: {e}")
    return 'OK'

# LINEからのテキスト受信
@handler.add(MessageEvent, message=TextMessage)
def handle_text(event):
    text = event.message.text.strip()

    if text.startswith("予想"):
        # 例：予想 北斗→+3200枚 / グール→-150枚
        prediction = "北斗102番台 / グール121番台"
        result = "北斗 +3200枚 / グール -150枚"
        save_gpt_log(event.source.user_id, prediction, result)
        reply = "予想と結果をDropboxに記録しました。"
    elif text.startswith("整理"):
        find_duplicates()
        reply = "Dropbox内の重複ファイルを整理しました。"
    else:
        reply = "ありがとうございます"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

# アプリ起動
if __name__ == "__main__":
    app.run()