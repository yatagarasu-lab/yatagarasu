import os
import hashlib
import json
import requests
from flask import Flask, request, abort

# LINEとDropbox連携
from linebot import LineBotApi
from linebot.models import TextSendMessage

app = Flask(__name__)

# LINE設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
USER_ID = os.getenv("LINE_USER_ID")
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)

# Dropbox設定
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# Dropboxからアクセストークン取得
def get_dropbox_access_token():
    url = "https://api.dropbox.com/oauth2/token"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": DROPBOX_REFRESH_TOKEN,
        "client_id": DROPBOX_APP_KEY,
        "client_secret": DROPBOX_APP_SECRET
    }
    response = requests.post(url, data=data)
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print("Dropboxトークン取得エラー:", response.text)
        return None

# ファイル一覧取得
def list_files(folder_path):
    access_token = get_dropbox_access_token()
    if not access_token:
        return []

    url = "https://api.dropboxapi.com/2/files/list_folder"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    data = {"path": folder_path}
    res = requests.post(url, headers=headers, json=data)

    if res.status_code == 200:
        return res.json()["entries"]
    else:
        print("ファイル一覧取得失敗:", res.text)
        return []

# ファイルダウンロード
def download_file(path):
    access_token = get_dropbox_access_token()
    if not access_token:
        return None

    url = "https://content.dropboxapi.com/2/files/download"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Dropbox-API-Arg": json.dumps({"path": path})
    }
    res = requests.post(url, headers=headers)

    if res.status_code == 200:
        return res.content
    else:
        print("ファイルダウンロード失敗:", res.text)
        return None

# ハッシュ計算
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# 重複チェックと削除
def find_duplicates(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    hash_map = {}

    for file in files:
        path = file["path_display"]
        content = download_file(path)
        if content is None:
            continue
        hash_value = file_hash(content)

        if hash_value in hash_map:
            print(f"重複ファイル検出: {path}（同一: {hash_map[hash_value]}）")
            delete_file(path)
            send_line(f"🗑️重複ファイル削除: {path}")
        else:
            hash_map[hash_value] = path

# Dropboxファイル削除
def delete_file(path):
    access_token = get_dropbox_access_token()
    if not access_token:
        return
    url = "https://api.dropboxapi.com/2/files/delete_v2"
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    data = {"path": path}
    res = requests.post(url, headers=headers, json=data)
    if res.status_code != 200:
        print("削除失敗:", res.text)

# LINE通知
def send_line(message):
    try:
        line_bot_api.push_message(USER_ID, TextSendMessage(text=message))
    except Exception as e:
        print("LINE送信エラー:", e)

# Webhook用
@app.route("/dropbox-webhook", methods=["GET", "POST"])
def dropbox_webhook():
    if request.method == "GET":
        return request.args.get("challenge")

    print("📦Dropbox更新検知!")
    send_line("📦Dropboxに更新がありました。解析を開始します。")
    find_duplicates("/Apps/slot-data-analyzer")
    return "", 200

# Dropbox 認証（Refreshトークン取得）
@app.route("/oauth2/callback")
def oauth2_callback():
    code = request.args.get("code")
    if not code:
        return "Error: No code provided", 400

    token_url = "https://api.dropbox.com/oauth2/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "https://slot-data-analyzer.onrender.com/oauth2/callback"
    }
    auth = (DROPBOX_APP_KEY, DROPBOX_APP_SECRET)
    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code != 200:
        return f"Error getting token: {response.text}", 400

    token_info = response.json()
    return f"""
    ✅ 認証成功！<br>
    Access Token: {token_info.get("access_token")}<br>
    🔁 Refresh Token: {token_info.get("refresh_token")}<br><br>
    🔒 この画面は保存せずに閉じてください。
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)