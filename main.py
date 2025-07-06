from flask import Flask, request, redirect
import requests
import os

app = Flask(__name__)

# Dropbox Appのクレデンシャル（Renderの環境変数に設定すること）
CLIENT_ID = os.getenv("DROPBOX_APP_KEY")
CLIENT_SECRET = os.getenv("DROPBOX_APP_SECRET")
REDIRECT_URI = "https://YOUR_RENDER_URL.onrender.com/oauth/callback"  # あなたの Render URL に変更

@app.route("/")
def index():
    return f'''
        <h1>Dropbox OAuth2 認証</h1>
        <a href="https://www.dropbox.com/oauth2/authorize?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}">
            Dropbox にログイン
        </a>
    '''

@app.route("/oauth/callback")
def oauth_callback():
    code = request.args.get("code")
    if not code:
        return "Error: code not found in callback URL", 400

    token_url = "https://api.dropboxapi.com/oauth2/token"
    data = {
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }

    auth = (CLIENT_ID, CLIENT_SECRET)
    response = requests.post(token_url, data=data, auth=auth)

    if response.status_code == 200:
        tokens = response.json()
        return f"""
            <h2>✅ 成功しました！</h2>
            <p><b>Access Token:</b> {tokens.get('access_token')}</p>
            <p><b>Refresh Token:</b> {tokens.get('refresh_token')}</p>
            <p>この情報を Render の環境変数に設定してください。</p>
        """
    else:
        return f"❌ エラー: {response.text}", 400

if __name__ == "__main__":
    app.run()