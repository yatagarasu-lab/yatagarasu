import os
import dropbox
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()  # .envから環境変数を読み込む

DROPBOX_ACCESS_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
GPT_API_KEY = os.getenv("OPENAI_API_KEY")
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"  # 使用フォルダ名

client = OpenAI(api_key=GPT_API_KEY)

def list_files(folder_path=DROPBOX_FOLDER):
    """Dropboxフォルダ内のファイル一覧を取得"""
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    res = dbx.files_list_folder(folder_path, recursive=True)
    files = [entry for entry in res.entries if isinstance(entry, dropbox.files.FileMetadata)]
    return sorted(files, key=lambda x: x.server_modified, reverse=True)

def download_file(path):
    """Dropbox上の指定ファイルをダウンロード"""
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    _, res = dbx.files_download(path)
    return res.content.decode("utf-8", errors="ignore")

def analyze_latest_file():
    """Dropboxの最新ファイルをGPTで解析"""
    try:
        files = list_files()
        if not files:
            return "Dropbox内にファイルが見つかりませんでした。"

        latest = files[0]
        print(f"🗂 最新ファイル: {latest.name}")

        content = download_file(latest.path_display)

        prompt = f"""以下のデータを読み取り、スロット設定や傾向について分析してください。
        
--- データ開始 ---
{content[:3000]}
--- データ終了（省略） ---
"""

        print("🤖 ChatGPT に送信中...")
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        summary = response.choices[0].message.content.strip()
        print("✅ 解析完了！")
        return summary

    except Exception as e:
        print(f"❌ 解析中にエラー発生: {e}")
        return f"解析中にエラーが発生しました: {e}"