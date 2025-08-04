# analyze_latest_file.py

from file_manager import organize_dropbox_files

def analyze_latest_file(dbx):
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

# デバッグ時のスタンドアロン実行用
if __name__ == "__main__":
    import dropbox

    # 🔧 ここで直接アクセストークンを記述 or 別ファイル・引数から受け取る
    access_token = "YOUR_ACCESS_TOKEN_HERE"  # <-- 差し替え用（環境変数は使わない）
    dbx = dropbox.Dropbox(access_token)

    analyze_latest_file(dbx)