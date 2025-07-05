from flask import Flask, request
import dropbox
import hashlib
import os
import openai
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# 環境変数から読み込み（Render に設定してください）
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.environ.get("LINE_USER_ID")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
openai.api_key = OPENAI_API_KEY


def list_files(folder_path="/Apps/slot-data-analyzer"):
    result = dbx.files_list_folder(folder_path)
    return result.entries


def download_file(file_path):
    metadata, res = dbx.files_download(file_path)
    return res.content


def file_hash(content):
    return hashlib.md5(content).hexdigest()


def is_duplicate(file_path, existing_hashes):
    content = download_file(file_path)
    hash_value = file_hash(content)
    if hash_value in existing_hashes:
        return True
    else:
        existing_hashes.add(hash_value)
        return False


def summarize_content(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "以下のデータを要約してください"},
                {"role": "user", "content": content.decode("utf-8", errors="ignore")}
            ],
            max_tokens=300
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"要約中にエラー: {str(e)}"


@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        return "Webhook確認成功", 200

    elif request.method == "POST":
        try:
            files = list_files()
            hashes = set()

            for file in files:
                path = file.path_display
                content = download_file(path)

                if is_duplicate(path, hashes):
                    dbx.files_delete_v2(path)
                    print(f"🗑️ 重複削除: {path}")
                    continue

                summary = summarize_content(content)
                line_bot_api.push_message(
                    LINE_USER_ID,
                    TextSendMessage(text=f"📝 {file.name}の要約:\n{summary}")
                )
                print(f"✅ 処理完了: {file.name}")

            return "", 200

        except Exception as e:
            print("❌ エラー:", str(e))
            return "Error", 500