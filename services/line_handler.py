import os
import dropbox
import mimetypes
from linebot import LineBotApi
from linebot.models import TextSendMessage

# Dropbox API認証
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")
DROPBOX_CLIENT_ID = os.environ.get("DROPBOX_CLIENT_ID")
DROPBOX_CLIENT_SECRET = os.environ.get("DROPBOX_CLIENT_SECRET")

def get_dropbox_access_token():
    from requests import post

    response = post(
        "https://api.dropboxapi.com/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": DROPBOX_REFRESH_TOKEN,
            "client_id": DROPBOX_CLIENT_ID,
            "client_secret": DROPBOX_CLIENT_SECRET,
        }
    )

    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        raise Exception(f"Failed to refresh Dropbox token: {response.text}")

def save_line_content_to_dropbox(event):
    line_bot_api = LineBotApi(os.environ.get("LINE_CHANNEL_ACCESS_TOKEN"))
    message_id = event.message.id
    user_id = event.source.user_id

    try:
        # ファイル取得
        content = line_bot_api.get_message_content(message_id)
        file_data = b"".join(chunk for chunk in content.iter_content())

        # ファイル名と拡張子推定
        if hasattr(event.message, 'file_name'):
            filename = event.message.file_name
        else:
            filename = f"{message_id}.jpg"  # 画像はjpg想定で保存

        dropbox_path = f"/LINE受信データ/{filename}"

        # Dropboxにアップロード
        dbx = dropbox.Dropbox(get_dropbox_access_token())
        dbx.files_upload(file_data, dropbox_path, mode=dropbox.files.WriteMode("overwrite"))

        # LINEへ返信（固定メッセージ）
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ありがとうございます")
        )

    except Exception as e:
        print(f"エラー: {e}")
        # 失敗時にユーザーに通知（任意）
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ファイルの保存に失敗しました")
        )