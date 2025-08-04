# log_utils.py

from datetime import datetime

# タイムスタンプ付きログ出力
def log(message):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{now} {message}")

# 成功メッセージ通知フォーマット
def format_success(file_path, summary):
    return f"✅ 新規ファイル検出\n📄 {file_path}\n📝 要約:\n{summary}"

# 重複検出メッセージ
def format_duplicate(file_path, original_path):
    return f"⚠️ 重複ファイル検出\n🗂 {file_path}\n📌 同一内容: {original_path}"

# エラーフォーマット
def format_error(context, detail=""):
    return f"❌ エラー: {context}\n🔍 詳細: {detail}"