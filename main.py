# main Flask entry point (to be populated below)
import os
import dropbox

# Dropboxのアクセストークン（RenderやReplitでは環境変数で設定）
DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

def load_project_memory():
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    file_path = "/Apps/slot-data-analyzer/プロジェクト指示書.txt"  # 保存場所に合わせて修正OK

    try:
        metadata, res = dbx.files_download(file_path)
        content = res.content.decode("utf-8")
        print("✅ プロジェクト記憶を読み込みました：\n", content)
        return content
    except Exception as e:
        print("❌ 指示書の読み込みに失敗:", e)
        return None

def main():
    memory = load_project_memory()
    if memory:
        # この部分に後でタスク振り分けなど追加していく
        pass

if __name__ == "__main__":
    main()