import os
import dropbox
import openai
import requests

# --- 環境変数 ---
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
TARGET_UPDATE_URL = os.environ.get("MAIN_UPDATE_URL")  # ← main.py の /update-code URL

# --- 初期化 ---
openai.api_key = OPENAI_API_KEY
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

# --- Dropboxからコード読み込み ---
def get_latest_code_from_dropbox(filename="new_main.py"):
    try:
        _, res = dbx.files_download(f"/{filename}")
        return res.content.decode("utf-8")
    except Exception as e:
        print(f"❌ Dropbox読み込み失敗: {e}")
        return None

# --- main.py をアップデート ---
def update_main_code(new_code):
    try:
        res = requests.post(TARGET_UPDATE_URL, data=new_code.encode("utf-8"))
        if res.status_code == 200:
            print("✅ main.py にアップデート成功")
        else:
            print(f"❌ main.py アップデート失敗: {res.text}")
    except Exception as e:
        print(f"❌ アップデート通信エラー: {e}")

# --- 実行 ---
if __name__ == "__main__":
    code = get_latest_code_from_dropbox("new_main.py")
    if code:
        update_main_code(code)