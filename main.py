from PIL import Image
from io import BytesIO

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    user_id = event.source.user_id
    message_id = event.message.id

    # 画像取得
    image_content = line_bot_api.get_message_content(message_id).content
    original_bytes = BytesIO(image_content)

    # Pillowで開いて圧縮
    image = Image.open(original_bytes)
    compressed = BytesIO()
    image.convert("RGB").save(compressed, format="JPEG", quality=85)
    compressed.seek(0)

    # Dropbox保存
    filename = f"{user_id}_{message_id}.jpg"
    dbx.files_upload(compressed.read(), f"/スロットデータ/{filename}")

    # 応答
    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text="ありがとうございます")
    )