import os
import dropbox
from io import BytesIO
from dropbox_dropin import get_dbx_client
from linebot import LineBotApi
from openai import OpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_random_exponential

load_dotenv()

# LINE連携
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
LINE_USER_ID = os.getenv("LINE_USER_ID")

# GPT連携
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

def save_image_to_dropbox(message_id):
    """LINEから画像を取得してDropboxへ保存"""
    content = line_bot_api.get_message_content(message_id)
    image_data = BytesIO()
    for chunk in content.iter_content():
        image_data.write(chunk)
    image_data.seek(0)

    dbx = get_dbx_client()
    filename = f"/Apps/slot-data-analyzer/line_image_{message_id}.jpg"
    dbx.files_upload(image_data.read(), filename, mode=dropbox.files.WriteMode("overwrite"))

@retry(wait=wait_random_exponential(min=1, max=5), stop=stop_after_attempt(3))
def analyze_dropbox_and_notify():
    """DropboxデータをGPTで解析し、LINEへ通知"""
    dbx = get_dbx_client()
    folder_path = "/Apps/slot-data-analyzer"

    # 最新ファイルを取得
    entries = dbx.files_list_folder(folder_path).entries
    if not entries:
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text="Dropboxにファイルが見つかりませんでした。"))
        return

    latest_file = sorted(entries, key=lambda x: x.server_modified, reverse=True)[0]
    _, res = dbx.files_download(latest_file.path_display)
    content = res.content.decode("utf-8", errors="ignore")

    # GPTで解析
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "スロットの設定データを解析してください"},
            {"role": "user", "content": content}
        ]
    )
    result = response.choices[0].message.content.strip()

    # LINEに送信
    line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=result))