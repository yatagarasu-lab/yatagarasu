# handle_image_message.py
from linebot.models import ImageMessage
import os
import tempfile
import dropbox

def handle_image_message(event, line_bot_api):
    message_id = event.message.id

    # 画像を一時ファイルに保存
    message_content = line_bot_api.get_message_content(message_id)
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        temp_file_path = tf.name

    # Dropbox にアップロード
    dbx = dropbox.Dropbox(os.environ.get("DROPBOX_ACCESS_TOKEN"))
    dropbox_path = f"/Apps/slot-data-analyzer/{message_id}.jpg"
    with open(temp_file_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path)

    # ユーザーに返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="画像を受け取り、Dropboxに保存しました。")
    )