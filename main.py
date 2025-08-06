import os
import dropbox
from flask import Flask, request

# 環境変数からDropboxの認証情報取得
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")

# Flaskアプリ作成
app = Flask(__name__)

# Dropboxセッション初期化
def get_dropbox():
    return dropbox.Dropbox(
        oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
        app_key=DROPBOX_APP_KEY,
        app_secret=DROPBOX_APP_SECRET
    )

dbx = get_dropbox()

# ファイル一覧取得（ルートフォルダ）
def list_files():
    try:
        res = dbx.files_list_folder(path="")
        return [entry.name for entry in res.entries]
    except Exception as e:
        return [f"❌ Dropbox一覧取得エラー: {e}"]

# 自動フォルダ作成処理（初期セットアップ）
def create_auto_folders():
    folders = [
        "/AutoCollected",
        "/AutoParsed",
        "/Logs",
        "/Screenshots",
        "/AI"
    ]
    created = []
    for path in folders:
        try:
            dbx.files_create_folder_v2(path)
            created.append(f"📁 作成: {path}")
        except dropbox.exceptions.ApiError as e:
            if "conflict" in str(e).lower():
                created.append(f"✅ 既に存在: {path}")
            else:
                created.append(f"❌ 作成失敗: {path} - {e}")
    return created

# Webhookエンドポイント
@app.route("/webhook", methods=["POST"])
def webhook():
    payload = request.get_json()
    print("📦 Webhook payload received:", payload)

    # Dropboxにログとして保存
    try:
        log_content = str(payload).encode("utf-8")
        filename = f"/Logs/webhook_log.txt"
        dbx.files_upload(log_content, filename, mode=dropbox.files.WriteMode.overwrite)
        return "✅ Webhook received and logged", 200
    except Exception as e:
        return f"❌ 保存エラー: {e}", 500

# 状態確認用エンドポイント
@app.route("/", methods=["GET"])
def index():
    files = list_files()
    return "<h2>✅ Yatagarasu 自動解析BOT 起動中</h2>" + "<br>".join(files)

# 自動フォルダ作成エンドポイント（初期化用）
@app.route("/init", methods=["GET"])
def init():
    result = create_auto_folders()
    return "<h2>📁 フォルダ初期化結果:</h2><pre>" + "\n".join(result) + "</pre>"

# Flask起動
if __name__ == "__main__":
    app.run()