import os
from utils.dropbox_utils import list_files
from services.processor import process_file

# Dropbox上のすべてのファイルを対象にGPT解析を実行する関数
def run_batch_processing(dbx, folder_path="/"):
    print(f"📁 フォルダ処理開始: {folder_path}")

    try:
        files = list_files(dbx, folder_path)
        print(f"🔍 {len(files)} 件のファイルが見つかりました")

        results = []
        for metadata in files:
            path_lower = metadata.path_lower
            result = process_file(dbx, metadata, path_lower)
            results.append(result)

        print("✅ バッチ処理完了")
        return results

    except Exception as e:
        print(f"❌ バッチ処理エラー: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
