import os
import dropbox
import openai
import time

# --- 認証情報 ---
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# --- 初期化 ---
openai.api_key = OPENAI_API_KEY

def get_dropbox():
    return dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )

dbx = get_dropbox()

# --- Dropbox フォルダ設定 ---
FOLDER_PATH = "/Apps/slot-data-analyzer"

# --- GPT解析処理 ---
def analyze_file(filename, content):
    prompt = f"以下のファイル内容を要約・分析し、スロット設定の予測や重要なポイントを抽出してください。\n\n{content}"
    try:
        res = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=3000
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ GPT解析エラー: {e}"

# --- メイン自動学習処理 ---
def auto_learn():
    try:
        result = dbx.files_list_folder(FOLDER_PATH)
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                path = entry.path_display
                _, res = dbx.files_download(path)
                content = res.content.decode("utf-8")

                print(f"\n📄 {entry.name} の内容を解析中...")
                analysis = analyze_file(entry.name, content)
                print(f"✅ 解析結果:\n{analysis}")
                time.sleep(1)  # GPT連続呼び出し対策
    except Exception as e:
        print(f"❌ 自動学習中にエラー: {e}")

if __name__ == "__main__":
    auto_learn()
