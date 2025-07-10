import os
import json
import hashlib
from flask import Flask, request, abort
import dropbox
from openai import OpenAI
from linebot import LineBotApi
from linebot.models import PushMessage, TextSendMessage

# 環境変数の取得
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
DROPBOX_FOLDER_PATH = "/Apps/slot-data-analyzer"
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# インスタンス生成
app = Flask(__name__)
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def download_file(path):
    _, res = dbx.files_download(path)
    return res.content.decode("utf-8", errors="ignore")

def list_files(folder_path):
    res = dbx.files_list_folder(folder_path)
    return res.entries

def analyze_content(content):
    prompt = f"""
次のファイルの内容を要約し、スロット設定・機種傾向・注目ポイントがあれば指摘してください：

--- 内容ここから ---
{content}
--- 内容ここまで ---

要点だけを簡潔にまとめてください。
"""
    completion = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return completion.choices[0].message.content.strip()

@app.route("/webhook", methods=["POST"])
def webhook():
    if not request.headers.get("X-Dropbox-Signature"):
        abort(400)

    data = json.loads(request.data.decode("utf-8"))
    for path in data.get("list_folder", {}).get("accounts", []):
        try:
            files = list_files(DROPBOX_FOLDER_PATH)
            if not files:
                continue
            latest_file = sorted(files, key=lambda f: f.server_modified)[-1]
            file_path = latest_file.path_display
            content = download_file(file_path)
            analysis = analyze_content(content)

            # LINE通知
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text=f"📊解析結果:\n{analysis}")
            )

            # Dropboxに結果を保存
            result_path = file_path.replace(".txt", "_解析結果.txt")
            dbx.files_upload(analysis.encode("utf-8"), result_path, mode=dropbox.files.WriteMode("overwrite"))

        except Exception as e:
            print("エラー:", e)

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=False)