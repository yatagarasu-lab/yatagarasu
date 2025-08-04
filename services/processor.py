import os
from utils.file_utils import load_file_content
from utils.duplicate_checker import is_duplicate
from services.gpt_summarizer import summarize_text, analyze_text

# 処理のメイン関数：Dropboxから取得したファイルの解析
def process_file(dbx, file_metadata, path_lower):
    print(f"📄 処理開始: {path_lower}")

    try:
        # ファイルの内容を取得
        file_content = load_file_content(dbx, path_lower)

        # 重複チェック
        if is_duplicate(file_content):
            print(f"⚠️ 重複ファイル（スキップ）: {path_lower}")
            return {
                "status": "duplicate",
                "path": path_lower
            }

        # 要約
        summary = summarize_text(file_content)

        # 解析
        analysis = analyze_text(file_content)

        print("✅ 処理完了")
        return {
            "status": "processed",
            "path": path_lower,
            "summary": summary,
            "analysis": analysis
        }

    except Exception as e:
        print(f"❌ 処理中エラー: {e}")
        return {
            "status": "error",
            "path": path_lower,
            "error": str(e)
        }
