from linebot.models import MessageEvent, ImageMessage, TextSendMessage
from dropbox_handler import upload_file
from gpt_handler import analyze_image
import tempfile
import os

# Flaskの@app.route(...) の下などに追加して使います
@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    try:
        # 一時ファイルに画像保存
        message_content = line_bot_api.get_message_content(event.message.id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf:
            for chunk in message_content.iter_content():
                tf.write(chunk)
            temp_file_path = tf.name

        # Dropboxにアップロード（例：画像ファイル名にタイムスタンプ使用）
        dropbox_path = f"/Apps/slot-data-analyzer/images/{os.path.basename(temp_file_path)}"
        upload_file(temp_file_path, dropbox_path)

        # GPTで解析
        result = analyze_image(temp_file_path)

        # 結果をLINEへ返信（上限4000文字）
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=result[:4000])
        )

        # 一時ファイル削除
        os.remove(temp_file_path)

    except Exception as e:
        print(f"画像処理エラー: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"⚠️ 画像処理中にエラー発生: {e}")
        )