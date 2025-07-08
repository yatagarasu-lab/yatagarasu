import os
import hashlib
import dropbox
import openai
import pytz
import requests
from PIL import Image
from flask import Flask, request, abort
from datetime import datetime
from dotenv import load_dotenv
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage
from linebot.v3.webhooks import MessageEvent, TextMessageContent, ImageMessageContent

# .envの読み込み
load_dotenv()

# 各種キー設定
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
channel_secret = os.getenv("LINE_CHANNEL_SECRET")
user_id = os.getenv("LINE_USER_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Flask アプリの初期化
app = Flask(__name__)

# LINE設定
configuration = Configuration(access_token=channel_access_token)
handler = WebhookHandler(channel_secret)

# Dropbox クライアント初期化（強化版）
def get_dropbox_client():
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")
    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")

    if refresh_token and app_key and app_secret:
        return dropbox.Dropbox(
            oauth2_refresh_token=refresh_token,
            app_key=app_key,
            app_secret=app_secret
        )
    else:
        # 古いアクセストークン方式にも対応
        access_token = os.getenv("DROPBOX_TOKEN")
        if access_token:
            return dropbox.Dropbox(access_token)
        else:
            raise Exception("Dropbox認証情報が設定されていません")

dbx = get_dropbox_client()

# 画像保存用フォルダ名
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

# ファイル保存
def save_file_to_dropbox(file_data, file_name):
    path = f"{DROPBOX_FOLDER}/{file_name}"
    dbx.files_upload(file_data, path, mode=dropbox.files.WriteMode("overwrite"))

# ハッシュ生成で重複判定
def file_hash(data):
    return hashlib.md5(data).hexdigest()

# 重複ファイルチェック
def find_duplicates(folder_path=DROPBOX_FOLDER):
    files = dbx.files_list_folder(folder_path).entries
    hash_map = {}
    for file in files:
        path = file.path_display
        _, res = dbx.files_download(path)
        content = res.content
        h = file_hash(content)
        if h in hash_map:
            print(f"重複ファイル検出: {path} = {hash_map[h]}")
            dbx.files_delete_v2(path)
        else:
            hash_map[h] = path

# LINE Webhook受信エンドポイント
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get("X-Line-Signature")
    if signature is None:
        print("⚠️ シグネチャが見つかりません。リクエストを拒否します。")
        abort(400)
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# イベント処理
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    text = event.message.text
    timestamp = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y%m%d_%H%M%S')
    filename = f"text_{timestamp}.txt"
    save_file_to_dropbox(text.encode(), filename)
    send_thanks(event.reply_token)

@handler.add(MessageEvent, message=ImageMessageContent)
def handle_image_message(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        message_content = line_bot_api.get_message_content(event.message.id)
        image_data = b''.join(chunk for chunk in message_content.iter_content())
    timestamp = datetime.now(pytz.timezone('Asia/Tokyo')).strftime('%Y%m%d_%H%M%S')
    filename = f"image_{timestamp}.jpg"
    save_file_to_dropbox(image_data, filename)
    find_duplicates()
    send_thanks(event.reply_token)

# 返信メッセージ
def send_thanks(token):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=token,
                messages=[TextMessage(text="ありがとうございます")]
            )
        )

# アプリ起動
if __name__ == "__main__":
    app.run()