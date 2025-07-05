from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler
from dropbox_handler import download_file, find_duplicates
from gpt_handler import analyze_zip_content

import os
import threading

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

USER_ID = os.getenv("LINE_USER_ID")
LOCK = threading.Lock()  # 排他制御用ロック

@app.route("/dropbox_webhook", methods=["POST"])
def handle_dropbox_webhook():
    if not LOCK.acquire(blocking=False):
        return "🔁 解析中のためスキップ", 429

    try:
        path = "/Apps/slot-data-analyzer/latest_upload.zip"
        zip_data = download_file(path)
        result = analyze_zip_content(zip_data)
        line_bot_api.push_message(USER_ID, TextSendMessage(text=result[:4000]))
        return "OK", 200

    except Exception as e:
        line_bot_api.push_message(USER_ID, TextSendMessage(text=f"❌ Webhookエラー: {e}"))
        return abort(500)

    finally:
        LOCK.release()

# 定時解析（夜21時）
def scheduled_analysis():
    if not LOCK.acquire(blocking=False):
        print("🔁 定時解析：同時実行防止のためスキップ")
        return

    try:
        path = "/Apps/slot-data-analyzer/latest_upload.zip"
        zip_data = download_file(path)
        result = analyze_zip_content(zip_data)
        line_bot_api.push_message(USER_ID, TextSendMessage(text=f"🕘定時解析結果:\n{result[:4000]}"))
    except Exception as e:
        line_bot_api.push_message(USER_ID, TextSendMessage(text=f"❌ 定時解析エラー: {e}"))
    finally:
        LOCK.release()

# 定時ジョブの起動
scheduler = BackgroundScheduler()
scheduler.add_job(scheduled_analysis, "cron", hour=21, minute=0)
scheduler.start()

@app.route("/health", methods=["GET"])
def health_check():
    return "✅ Server is running", 200

if __name__ == "__main__":
    app.run()