# handle_image_message.py

from linebot.models import TextSendMessage
import os
import tempfile
import dropbox

def handle_image_message(event, line_bot_api):
    message_id = event.message.id

    # 画像取得
    message_content = line_bot_api.get_message_content(message_id)

    # 一時ファイルへ保存
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        temp_file_path = tf.name

    # Dropboxへアップロード
    dropbox_token = os.environ.get("DROPBOX_ACCESS_TOKEN")
    dbx = dropbox.Dropbox(dropbox_token)
    dropbox_path = f"/Apps/slot-data-analyzer/{message_id}.jpg"
    with open(temp_file_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

    # ユーザーへ返信
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="画像を受け取り、Dropboxに保存しました。")
    )