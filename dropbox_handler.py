import os
import dropbox
from linebot import LineBotApi
from linebot.models import TextSendMessage
from dropbox_utils import list_files, download_file
from gpt_utils import summarize_text

# 環境変数の読み込み
DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")  # push送信先ユーザー

# インスタンス作成
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Dropbox更新時の処理関数
def handle_dropbox_update():
    try:
        print("🔍 Dropbox更新を検知、ファイル一覧を取得中...")
        files = list_files()

        if not files:
            print("❗ファイルが存在しません。")
            return

        latest_file = sorted(files, key=lambda f: f.server_modified, reverse=True)[0]
        print(f"📦 最新ファイル: {latest_file.name}")

        content = download_file(latest_file.path_display).decode("utf-8", errors="ignore")

        print("🧠 GPTで解析中...")
        summary = summarize_text(content)

        message = f"📂 最新ファイル: {latest_file.name}\n\n📝 要約:\n{summary}"
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))

        print("✅ LINE通知完了")
    except Exception as e:
        error_message = f"[Dropbox処理エラー]: {str(e)}"
        print(error_message)
        line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=error_message))