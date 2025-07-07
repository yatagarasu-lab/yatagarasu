import os
from dropbox_utils import list_files, download_file
from gpt_utils import summarize_text, is_duplicate
from line_utils import send_line_message

# 監視フォルダ
FOLDER_PATH = "/Apps/slot-data-analyzer"

# 保存済みファイル内容キャッシュ（実際の運用ではDB等で管理推奨）
processed_files = {}

def handle_new_files():
    print("📂 Dropboxフォルダを確認中...")
    try:
        entries = list_files(FOLDER_PATH)
        for entry in entries:
            path = entry.path_display
            if path in processed_files:
                continue  # すでに処理済み

            print(f"📥 新ファイル検出: {path}")
            content = download_file(path)

            # 重複チェック
            if is_duplicate(content, processed_files.values()):
                print("⚠️ 重複ファイルとしてスキップ")
                continue

            # GPTで要約
            summary = summarize_text(content.decode(errors="ignore"))
            print(f"📝 要約結果: {summary}")

            # LINEへ通知
            send_line_message(f"📄 新ファイル: {os.path.basename(path)}\n📝 要約: {summary}")

            # 処理済みに追加
            processed_files[path] = content

    except Exception as e:
        print(f"[ファイル処理エラー]: {e}")