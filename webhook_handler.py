import json
import dropbox
from flask import request
from gpt_analyzer import analyze_and_notify

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

# Webhookエンドポイントの処理
def handle_webhook():
    # DropboxのWebhook検証用（GET）
    if request.method == "GET":
        challenge = request.args.get("challenge")
        return challenge, 200

    # 通知内容（POST）
    if request.method == "POST":
        try:
            body = request.data.decode("utf-8")
            data = json.loads(body)
            user_id = data.get("list_folder", {}).get("accounts", [])[0]

            # Dropbox APIを使って最新ファイルを取得
            dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
            entries = dbx.files_list_folder(path="/Apps/slot-data-analyzer").entries

            if entries:
                latest_file = sorted(entries, key=lambda f: f.client_modified, reverse=True)[0]
                file_path = latest_file.path_display

                # GPT解析＋LINE通知を実行
                analyze_and_notify(dbx, file_path)

        except Exception as e:
            print("Webhook処理中にエラー:", e)
            return "Error", 500

        return "OK", 200