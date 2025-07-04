# handle_image_message.py

from linebot.models import ImageMessage, TextSendMessage
from linebot import LineBotApi
from dropbox_handler import upload_to_dropbox

import tempfile
import os
import requests

def handle_image_message(event, line_bot_api: LineBotApi):
    """LINEからの画像を一時保存しDropboxへアップロードする"""
    try:
        # 画像データを一時ファイルに保存
        message_content = line_bot_api.get_message_content(event.message.id)
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            for chunk in message_content.iter_content():
                tf.write(chunk)
            temp_path = tf.name

        # ファイル名をユーザーIDとメッセージIDから作成
        file_name = f"{event.source.user_id}_{event.message.id}.jpg"
        dropbox_path = f"/Apps/slot-data-analyzer/images/{file_name}"

        # Dropboxへアップロード
        upload_to_dropbox(temp_path, dropbox_path)

        # ユーザーに返信
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="📷 画像をDropboxに保存しました！")
        )

        # 一時ファイルを削除
        os.remove(temp_path)

    except Exception as e:
        print(f"画像処理エラー: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"⚠️ 画像の保存に失敗しました: {e}")
        )