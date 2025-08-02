import os
import datetime
import dropbox
import requests
from flask import Flask, request, abort

# Flaskアプリの作成
app = Flask(__name__)

# Dropboxアクセストークンの取得（リフレッシュトークンを使って）
def get_dropbox_access_token():
    client_id = os.getenv("DROPBOX_CLIENT_ID")
    client_secret = os.getenv("DROPBOX_CLIENT_SECRET")
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")

    if not client_id or not client_secret or not refresh_token:
        raise Exception("Dropbox認証情報が不足しています。")

    token_url = "https://api.dropbox.com/oauth2/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    response = requests.post(token_url, headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

# GPTの出力をDropboxに保存
def save_gpt_output_to_dropbox(content: str, filename_prefix="gpt_log"):
    try:
        access_token = get_dropbox_access_token()
        dbx = dropbox.Dropbox(access_token)

        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/Apps/slot-data-analyzer/{filename_prefix}_{now}.txt"
        dbx.files_upload(content.encode("utf-8"), filename, mode=dropbox.files.WriteMode.overwrite)

        print(f"✅ GPT出力ログをDropboxに保存しました: {filename}")
    except Exception as e:
        print(f"❌ Dropbox保存エラー: {e}")

# Webhook用のルート（今後LINEなどと連携する際に利用）
@app.route("/", methods=["POST"])
def webhook():
    if not request.is_json:
        abort(400)

    data = request.get_json()
    gpt_output = data.get("text", "（内容がありません）")

    save_gpt_output_to_dropbox(gpt_output)

    return "OK", 200

# テスト用ルート（直接叩いて動作確認）
@app.route("/", methods=["GET"])
def hello():
    return "GPT to Dropbox 保存BOT 稼働中", 200

# アプリ起動（Renderなどで使用）
if __name__ == "__main__":
    app.run(debug=True)