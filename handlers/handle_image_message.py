from linebot.models import ImageMessage
from linebot.models.events import MessageEvent
from linebot.exceptions import LineBotApiError
from io import BytesIO
import zipfile
import time

from dropbox_handler import upload_file
from gpt_handler import analyze_zip_content

def handle_image_message(event, line_bot_api, USER_ID):
    """画像メッセージを受信し、DropboxにZIP形式で保存 → GPT解析 → LINE通知"""
    try:
        # 画像を取得
        message_id = event.message.id
        message_content = line_bot_api.get_message_content(message_id)
        image_data = b''.join(chunk for chunk in message_content.iter_content(chunk_size=1024))

        # 一時ZIPファイル作成
        timestamp = int(time.time())
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.writestr(f"image_{timestamp}.jpg", image_data)

        zip_bytes = zip_buffer.getvalue()

        # Dropboxにアップロード
        dropbox_path = "/Apps/slot-data-analyzer/latest_upload.zip"
        upload_file(zip_bytes, dropbox_path)

        # GPTでZIP解析
        result = analyze_zip_content(zip_bytes)

        # LINEへ送信（文字数制限あり）
        line_bot_api.push_message(USER_ID, TextSendMessage(text=result[:4000]))

    except LineBotApiError as e:
        print(f"⚠️ LINE APIエラー: {e}")
        line_bot_api.push_message(USER_ID, TextSendMessage(text="⚠️ LINE画像処理中にエラーが発生しました"))
    except Exception as e:
        print(f"⚠️ 画像処理エラー: {e}")
        line_bot_api.push_message(USER_ID, TextSendMessage(text=f"⚠️ 画像処理中にエラーが発生しました: {e}"))
