import os
import dropbox
from datetime import datetime
from linebot import LineBotApi
from linebot.models import MessageEvent, ImageMessage, FileMessage

# 環境変数
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Dropboxアクセストークン取得
def get_dropbox_client():
    from services.dropbox_auth import refresh_dropbox_access_token
    access_token = refresh_dropbox_access_token()
    return dropbox.Dropbox(oauth2_access_token=access_token)

# LINEの画像やファイルをDropboxに保存する
def save_line_content_to_dropbox(event: MessageEvent):
    message = event.message
    user_id = event.source.user_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if isinstance(message, ImageMessage):
        ext = "jpg"
        filename = f"{timestamp}_img_from_{user_id}.{ext}"
    elif isinstance(message, FileMessage):
        ext = message.file_name.split('.')[-1] if '.' in message.file_name else "bin"
        filename = f"{timestamp}_{message.file_name}"
    else:
        print("対応していないメッセージ形式です")
        return

    # LINEからコンテンツ取得
    content = line_bot_api.get_message_content(message.id)
    file_data = content.content

    # Dropboxへ保存
    dbx = get_dropbox_client()
    dropbox_path = f"/Apps/slot-data-analyzer/{filename}"
    dbx.files_upload(file_data, dropbox_path, mode=dropbox.files.WriteMode.overwrite)
    print(f"✅ 保存完了: {dropbox_path}")