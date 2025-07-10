import os
import time
import dropbox
import hashlib
from openai import OpenAI
from linebot import LineBotApi
from linebot.models import TextSendMessage
from dropbox_handler import list_files, download_file, delete_file

# OpenAIクライアント設定
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# LINE API
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Dropbox クライアント
dbx = dropbox.Dropbox(
    oauth2_refresh_token=os.getenv("DROPBOX_REFRESH_TOKEN"),
    app_key=os.getenv("DROPBOX_APP_KEY"),
    app_secret=os.getenv("DROPBOX_APP_SECRET")
)

# 重複ファイルのハッシュを記録
hash_registry = {}

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def analyze_and_notify():
    folder_path = "/Apps/slot-data-analyzer"
    files = list_files(folder_path)

    for file in files:
        path = file.path_display
        content = download_file(path)

        # 重複チェック
        h = file_hash(content)
        if h in hash_registry:
            print(f"[SKIP] 重複ファイル: {path}")
            delete_file(path)  # 自動削除
            continue
        hash_registry[h] = path

        # GPTによる要約/解析
        text = content.decode("utf-8", errors="ignore")[:3000]
        print(f"[INFO] GPT解析中: {path}")

        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "これはスロットの設定やイベント情報のファイルです。内容を分析・要約してください。"},
                    {"role": "user", "content": text}
                ],
                temperature=0.4,
                max_tokens=1000
            )
            summary = response.choices[0].message.content.strip()

            # LINE通知送信
            line_bot_api.push_message(
                LINE_USER_ID,
                TextSendMessage(text=f"📄 {path} を解析しました:\n\n{summary}")
            )
            print(f"[通知完了] {path}")

        except Exception as e:
            print(f"[エラー] GPTまたはLINE通知失敗: {e}")

        time.sleep(1)  # 負荷対策