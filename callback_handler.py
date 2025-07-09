import os
from linebot.models import MessageEvent, TextMessage, ImageMessage
from utils import reply_text_message, reply_image_message
import dropbox
from datetime import datetime

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_LOG_FOLDER = "/logs"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def handle_text_event(event: MessageEvent):
    user_id = event.source.user_id
    user_text = event.message.text

    # ChatGPT応答
    reply_text = reply_text_message(user_text)

    # LINEへ返信
    reply_image_message(event.reply_token, reply_text)

    # Dropboxログ保存
    log_message_to_dropbox(user_id, user_text, reply_text)


def handle_image_event(event: MessageEvent):
    user_id = event.source.user_id
    reply_text = "画像を受け取りました（解析準備中）"
    reply_image_message(event.reply_token, reply_text)

    # ログにも画像受付情報を記録
    log_message_to_dropbox(user_id, "[画像]", reply_text)


def log_message_to_dropbox(user_id, user_text, reply_text):
    """
    受信メッセージと応答内容をDropboxにログとして保存（1日1ファイル）
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_path = f"{DROPBOX_LOG_FOLDER}/{date_str}"
    filename = f"{user_id}.log"
    full_path = f"{log_path}/{filename}"

    log_entry = f"[{datetime.now().strftime('%H:%M:%S')}]\nUSER: {user_text}\nGPT : {reply_text}\n\n"

    try:
        # 既存ファイルがあるかチェック
        try:
            _, res = dbx.files_download(full_path)
            existing = res.content.decode("utf-8")
        except dropbox.exceptions.ApiError:
            existing = ""

        updated_log = existing + log_entry
        dbx.files_upload(updated_log.encode("utf-8"), full_path, mode=dropbox.files.WriteMode.overwrite)
        print("✅ ログ記録成功")
    except Exception as e:
        print(f"❌ ログ記録失敗: {e}")