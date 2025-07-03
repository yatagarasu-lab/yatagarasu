import os
import dropbox
import hashlib
from flask import Flask, request
from linebot import LineBotApi
from linebot.models import TextSendMessage
import openai

# 環境変数からトークン取得（Render環境変数で設定）
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
openai.api_key = OPENAI_API_KEY

# 既存ファイルのハッシュを保存（重複確認用）
known_hashes = set()

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def summarize_content(text):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "次のファイルの内容を要約してください。"},
            {"role": "user", "content": text}
        ]
    )
    return response.choices[0].message.content.strip()

@app.route("/webhook", methods=["POST"])
def webhook():
    # Dropbox Webhook：ファイル変更イベントを受け取る
    delta = request.get_json()
    if not delta or "list_folder" not in delta:
        return "No relevant data", 400

    # 変更されたユーザーのアカウントID（必ずしも必要ではない）
    for account_id in delta["list_folder"]["accounts"]:
        # 特定フォルダ（Apps/slot-data-analyzer）内のファイルを取得
        result = dbx.files_list_folder("/Apps/slot-data-analyzer")
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                _, res = dbx.files_download(entry.path_display)
                content = res.content
                h = file_hash(content)
                if h in known_hashes:
                    continue  # 重複なのでスキップ
                known_hashes.add(h)

                try:
                    text = content.decode("utf-8", errors="ignore")
                except Exception:
                    text = "[バイナリファイル] 内容の解析不可"

                summary = summarize_content(text)

                # LINE通知送信
                line_bot_api.push_message(
                    LINE_USER_ID,
                    TextSendMessage(text=f"📦新しいファイル: {entry.name}\n📄要約:\n{summary}")
                )

    return "OK", 200

if __name__ == "__main__":
    app.run(debug=True)