from flask import Flask, request, jsonify
import os
import dropbox
import hashlib
from datetime import datetime, timedelta
import pytz
from linebot import LineBotApi
from linebot.models import TextSendMessage
import openai
import threading
import time
import requests

app = Flask(__name__)

# ====== 環境変数 ======
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")
openai.api_key = os.getenv("OPENAI_API_KEY")
TIMEZONE = pytz.timezone("Asia/Tokyo")

# ====== 初期化 ======
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# ====== ファイルの要約と予測 ======
def summarize_and_predict(text):
    prompt = f"""
これはスロット実戦データまたは設定に関する情報です。
内容を簡潔に要約し、設定傾向や今後の予測を含めて解釈してください。
その後、次回の高設定が入りそうな機種または台番号を1つでもいいので予測してください。

内容:
{text}

出力形式：
【要約】
...
【次回予測】
...
    """
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# ====== ファイルのダウンロード ======
def download_file(path):
    _, res = dbx.files_download(path)
    return res.content.decode("utf-8", errors="ignore")

# ====== ハッシュによる重複チェック ======
hash_memory = {}

def file_hash(content):
    return hashlib.md5(content.encode("utf-8")).hexdigest()

def is_duplicate(file_name, content):
    h = file_hash(content)
    if h in hash_memory:
        return True
    hash_memory[h] = file_name
    return False

# ====== 通知処理 ======
def send_line_message(text):
    message = TextSendMessage(text=text)
    line_bot_api.push_message(USER_ID, message)

# ====== Webhook受信時の処理 ======
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    for entry in data["list_folder"]["entries"]:
        if entry[0] == "file":
            path = entry[1]
            try:
                content = download_file(path)
                if is_duplicate(path, content):
                    print(f"重複ファイル検出: {path}")
                    return jsonify({"status": "duplicate"})
                result = summarize_and_predict(content)
                message = f"📂 新規ファイル: {path}\n\n{result}"
                send_line_message(message)
            except Exception as e:
                print("解析失敗:", e)
    return jsonify({"status": "ok"})

# ====== OpenAI使用量（円換算） ======
def get_current_usage():
    try:
        headers = {
            "Authorization": f"Bearer {openai.api_key}"
        }
        now = datetime.now()
        start = now.replace(day=1).strftime("%Y-%m-%d")
        end = now.strftime("%Y-%m-%d")
        url = f"https://api.openai.com/v1/dashboard/billing/usage?start_date={start}&end_date={end}"
        res = requests.get(url, headers=headers)
        usage_usd = res.json().get("total_usage", 0) / 100.0
        usage_jpy = round(usage_usd * 160, 2)
        return f"${usage_usd:.2f}（約￥{usage_jpy}）"
    except Exception as e:
        return f"取得失敗: {e}"

# ====== 毎週日曜19時に料金通知 ======
def schedule_billing_notice():
    def job():
        while True:
            now = datetime.now(TIMEZONE)
            if now.weekday() == 6 and now.hour == 19 and now.minute == 0:
                usage = get_current_usage()
                send_line_message(f"💰 今週のOpenAI料金使用状況：\n{usage}")
            time.sleep(60)
    threading.Thread(target=job, daemon=True).start()

# ====== アプリ起動時に定期処理スタート ======
schedule_billing_notice()

# ====== 動作確認用ルート ======
@app.route("/", methods=["GET"])
def index():
    return "GPT解析BOT 起動中"

if __name__ == "__main__":
    app.run()