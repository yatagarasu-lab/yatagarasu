import schedule
import time
import os
from dropbox_handler import list_files, download_file
from gpt_handler import analyze_zip_content
from linebot import LineBotApi
from linebot.models import TextSendMessage

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
USER_ID = os.getenv("LINE_USER_ID")  # 通知先ユーザーID

def daily_analysis():
    try:
        folder_path = "/Apps/slot-data-analyzer"
        files = list_files(folder_path)
        if not files:
            print("解析対象のファイルがありません。")
            return

        # 最新のファイルだけ解析（ZIP前提）
        latest_file = sorted(files, key=lambda x: x.server_modified)[-1]
        zip_data = download_file(latest_file.path_display)
        result = analyze_zip_content(zip_data)

        # 通知
        line_bot_api.push_message(
            USER_ID,
            TextSendMessage(text=f"📊 定時解析結果:\n{result[:4000]}")
        )
        print("定時解析＆通知が完了しました。")
    except Exception as e:
        print(f"定時解析エラー: {e}")
        line_bot_api.push_message(
            USER_ID,
            TextSendMessage(text=f"⚠️ 定時解析中にエラー発生: {e}")
        )

# 毎日 21:00 に実行
schedule.every().day.at("21:00").do(daily_analysis)

if __name__ == "__main__":
    print("⏰ 定時解析スケジューラ起動中...")
    while True:
        schedule.run_pending()
        time.sleep(30)
