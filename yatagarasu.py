import os
import dropbox
from file_manager import organize_dropbox_files

DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN")
dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)

def analyze_latest_file():
    latest_file = organize_dropbox_files()
    if not latest_file:
        print("❌ 解析対象ファイルが見つかりませんでした。")
        return

    path = latest_file.path_display
    metadata, res = dbx.files_download(path)
    content = res.content.decode("utf-8", errors="ignore")  # 画像ではなくテキスト前提

    # GPTによる解析処理（仮想処理）
    print(f"📊 ファイル名: {latest_file.name}")
    print(f"📥 コンテンツ一部:\n{content[:500]}")  # 上限500文字を表示

    # ここでGPT APIによる要約や構造解析を追加できます（省略中）
    print("✅ 解析完了")

# デバッグ時に単体実行可能にする
if __name__ == "__main__":
    analyze_latest_file()