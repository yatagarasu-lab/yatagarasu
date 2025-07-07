import os
import dropbox
from dropbox.files import FileMetadata
from linebot import LineBotApi
from linebot.models import TextSendMessage
from gpt_utils import summarize_text
from dropbox_utils import list_files, download_file

# LINE通知設定
LINE_USER_ID = os.getenv("LINE_USER_ID")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Dropbox接続
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

# 対象フォルダ
FOLDER_PATH = "/Apps/slot-data-analyzer"

def handle_new_files():
    """
    Dropboxフォルダ内の全ファイルを取得して、
    テキスト・画像ファイルをGPTで要約し、LINE通知する。
    """
    print("📂 Dropboxのファイル一覧を取得中...")
    files = list_files(FOLDER_PATH)

    for entry in files:
        if isinstance(entry, FileMetadata):
            path = entry.path_display
            print(f"📄 処理対象ファイル: {path}")

            # ファイル内容を取得
            content = download_file(path)

            # テキストファイルの場合のみ処理
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                print("🔍 画像などの非テキストファイルはスキップ")
                continue

            # GPTで要約
            summary = summarize_text(text)

            # LINEに通知
            message = f"📩 ファイル名: {os.path.basename(path)}\n📄 要約:\n{summary}"
            line_bot_api.push_message(LINE_USER_ID, TextSendMessage(text=message))
            print("✅ LINE通知完了")

    return "完了"