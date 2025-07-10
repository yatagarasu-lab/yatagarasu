import os
import dropbox
from dotenv import load_dotenv
from linebot import LineBotApi
from utils import download_and_analyze_files
from predictor import run_prediction_cycle

load_dotenv()

# 環境変数の読み込み
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_ACCESS_TYPE = "refresh_token"

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# Dropbox接続（リフレッシュトークン方式）
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

def process_dropbox_change():
    """Dropbox上のファイル更新を検出して処理"""
    result = download_and_analyze_files(dbx)

    if result:
        line_bot_api.push_message(LINE_USER_ID, result)

def daily_cycle():
    """毎日の予測→答え合わせ→学習→通知の流れ"""
    result = run_prediction_cycle()
    if result:
        line_bot_api.push_message(LINE_USER_ID, result)

if __name__ == "__main__":
    print("メイン処理が直接起動されました。")