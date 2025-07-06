from flask import Flask, request
import requests
import os

app = Flask(__name__)

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
REDIRECT_URI = "https://slot-data-analyzer.onrender.com/oauth2/callback"

@app.route("/oauth2/callback")
def oauth2_callback():
    code = request.args.get("code")
    if not code:
        return "Error: No code provided", 400

    token_url = "https://api.dropbox.com/oauth2/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    auth = (DROPBOX_APP_KEY, DROPBOX_APP_SECRET)

    response = requests.post(token_url, data=data, auth=auth)
    if response.status_code != 200:
        return f"Error getting token: {response.text}", 400

    token_info = response.json()
    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")

    print("✅ Access Token:", access_token)
    print("🔁 Refresh Token:", refresh_token)

    return "認証完了しました！この画面は閉じてOKです。"