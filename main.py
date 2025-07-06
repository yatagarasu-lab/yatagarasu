from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# ▼ Dropboxのアプリキー、シークレット、リフレッシュトークン（環境変数で管理推奨）
APP_KEY = os.getenv("DROPBOX_APP_KEY", "YOUR_APP_KEY")
APP_SECRET = os.getenv("DROPBOX_APP_SECRET", "YOUR_APP_SECRET")
REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN", "YOUR_REFRESH_TOKEN")

@app.route("/")
def home():
    return "LINE×Dropbox GPTサーバー起動中"

# ▼ Dropboxのrefresh_tokenが有効か確認するエンドポイント
@app.route("/check_token", methods=["GET"])
def check_token():
    try:
        response = requests.post(
            "https://api.dropboxapi.com/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": REFRESH_TOKEN
            },
            auth=(APP_KEY, APP_SECRET)
        )

        if response.status_code == 200:
            access_token = response.json().get("access_token")
            return jsonify({
                "status": "valid",
                "message": "✅ refresh_token は有効です",
                "access_token": access_token
            }), 200
        else:
            return jsonify({
                "status": "invalid",
                "message": "❌ refresh_token が無効です",
                "error": response.json()
            }), 401

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": "⚠️ チェック中にエラーが発生しました",
            "details": str(e)
        }), 500

# 既存の他のエンドポイント（/webhook など）があればここに追記