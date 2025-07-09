import os
import json
from datetime import datetime
import dropbox
from dotenv import load_dotenv

load_dotenv()

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
DROPBOX_LOG_FOLDER = "/logs"

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)


def save_log_to_dropbox(message_type, content, user_id="unknown_user"):
    """
    任意のメッセージやGPT応答などをDropboxに日付別で保存する

    Parameters:
        message_type (str): "user", "gpt", "system", "image", etc.
        content (str): 保存するテキスト内容
        user_id (str): LINEのユーザーIDなど（省略可能）
    """

    now = datetime.now()
    date_folder = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%H-%M-%S")
    filename = f"{timestamp}_{message_type}_{user_id}.txt"

    dropbox_path = f"{DROPBOX_LOG_FOLDER}/{date_folder}/{filename}"
    local_temp = f"/tmp/{filename}"

    try:
        # 一時ファイルに保存
        with open(local_temp, "w", encoding="utf-8") as f:
            f.write(content)

        # Dropboxにアップロード（上書き）
        with open(local_temp, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)

        print(f"✅ ログ保存成功: {dropbox_path}")
        return True

    except Exception as e:
        print(f"❌ Dropboxへのログ保存エラー: {e}")
        return False
