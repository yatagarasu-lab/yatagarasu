from datetime import datetime
import dropbox
import os

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_LOG_FOLDER = "/logs"
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)


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
