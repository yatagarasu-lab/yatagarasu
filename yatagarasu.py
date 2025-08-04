from file_manager import organize_dropbox_files, get_dropbox_client

def analyze_latest_file():
    dbx = get_dropbox_client()
    latest_file = organize_dropbox_files("/")
    if not latest_file:
        print("❌ 解析対象ファイルが見つかりません。")
        return

    path = latest_file.path_display
    metadata, res = dbx.files_download(path)
    content = res.content.decode("utf-8", errors="ignore")

    print(f"📊 ファイル名: {latest_file.name}")
    print(f"📥 コンテンツ一部:\n{content[:500]}")
    print("✅ 解析完了")

if __name__ == "__main__":
    analyze_latest_file()