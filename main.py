import os
import hashlib
import dropbox
import openai
from flask import Flask, request
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# 環境変数
LINE_USER_ID = os.getenv("LINE_USER_ID")
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# APIキー設定
openai.api_key = OPENAI_API_KEY
dbx = dropbox.Dropbox(DROPBOX_TOKEN)

app = Flask(__name__)

# ハッシュで重複判定
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def upload_to_dropbox(filename, content):
    existing_files = dbx.files_list_folder("/Apps/slot-data-analyzer").entries
    existing_hashes = {file_hash(dbx.files_download(f.path_lower)[1].content): f.name for f in existing_files if isinstance(f, dropbox.files.FileMetadata)}

    new_hash = file_hash(content)
    if new_hash in existing_hashes:
        print("✅ 重複ファイル検出:", existing_hashes[new_hash])
        return False
    dbx.files_upload(content, f"/Apps/slot-data-analyzer/{filename}", mute=True)
    print("✅ Dropboxに保存:", filename)
    return True

def summarize_with_gpt(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": f"以下を要約してください：\n{text}"}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI API エラー:", str(e))
        return "解析に失敗しました。"

@app.route('/')
def home():
    return '🏠 GPT連携サーバー 起動中！'

@app.route('/dropbox-test')
def dropbox_test():
    return 'Dropbox test OK', 200

@app.route('/callback', methods=['POST'])
def callback():
    body = request.json

    if not body or 'events' not in body:
        return 'Invalid data', 400

    event = body['events'][0]
    user_message = event['message'].get('text', '')

    # GPT要約実行
    summary = summarize_with_gpt(user_message)

    # Dropbox保存（重複チェック）
    filename = f"{event['timestamp']}.txt"
    upload_to_dropbox(filename, user_message.encode())

    # LINEへの返信内容（今は省略 / 後でPush APIで送信可能）
    print("📩 ユーザー:", user_message)
    print("🧠 GPT要約:", summary)

    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)