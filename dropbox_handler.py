import os
import json
from dropbox import Dropbox
from analyze_file import analyze_file
from line_push import send_line_message
from utils import is_duplicate, save_hash
from dotenv import load_dotenv

load_dotenv()

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
MONITOR_FOLDER = os.getenv("DROPBOX_MONITOR_FOLDER", "/Apps/slot-data-analyzer")

dbx = Dropbox(DROPBOX_ACCESS_TOKEN)

def handle_dropbox_webhook(request):
    body = json.loads(request.data.decode("utf-8"))

    for account in body.get("list_folder", {}).get("accounts", []):
        print(f"📥 更新を検知したアカウント: {account}")
        process_recent_files()

def process_recent_files():
    try:
        entries = dbx.files_list_folder(MONITOR_FOLDER, recursive=False).entries
    except Exception as e:
        print(f"❌ Dropboxフォルダ読み込み失敗: {e}")
        return

    for entry in entries:
        if hasattr(entry, "path_lower") and not entry.name.startswith("."):
            file_path = entry.path_display
            print(f"🔍 ファイル検出: {file_path}")

            # 重複チェック
            content, res = None, None
            try:
                _, res = dbx.files_download(file_path)
                content = res.content
            except Exception as e:
                print(f"❌ ダウンロード失敗: {e}")
                continue

            if is_duplicate(content):
                print(f"⚠️ 重複ファイル: {file_path}")
                continue
            else:
                save_hash(content)

            try:
                result = analyze_file(file_path)
                if os.getenv("LINE_PUSH_ENABLED", "true").lower() == "true":
                    send_line_message(f"✅ 解析完了: {os.path.basename(file_path)}\n\n{result[:300]}...")
            except Exception as e:
                print(f"❌ ファイル解析エラー: {e}")