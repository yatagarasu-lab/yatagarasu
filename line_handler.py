import os
import hashlib
import base64
import requests
from flask import request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, ImageMessage, TextSendMessage

from dropbox_handler import upload_file, file_exists, get_file_hash, delete_file

# 環境変数からLINEの情報を読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Dropbox内の保存フォルダ
FOLDER_PATH = "/Apps/slot-data-analyzer"

# メインのイベント処理
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    # ユーザーIDと画像IDでファイル名を作成
    user_id = event.source.user_id
    message_id = event.message.id
    file_name = f"{user_id}_{message_id}.jpg"

    # LINEの画像取得
    image_content = line_bot_api.get_message_content(message_id)
    file_data = image_content.content

    # 重複チェックのためハッシュ化
    new_hash = hashlib.sha256(file_data).hexdigest()

    # Dropbox内のファイルをチェック
    entries = file_exists(FOLDER_PATH)
    for entry in entries:
        if not entry.name.endswith(".jpg"):
            continue
        existing_data = get_file_hash(f"{FOLDER_PATH}/{entry.name}")
        if new_hash == hashlib.sha256(existing_data).hexdigest():
            # 重複ファイルなら保存しない
            reply = "重複ファイルのため保存されませんでした。"
            break
    else:
        # Dropboxにアップロード
        upload_file(file_name, file_data)
        reply = "画像をDropboxに保存しました。"

    # ユーザーに返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply)
    )