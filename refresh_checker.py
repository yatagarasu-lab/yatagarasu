import requests

# ▼ 以下を書き換えて使用
APP_KEY = 'YOUR_APP_KEY'             # Dropbox App Key
APP_SECRET = 'YOUR_APP_SECRET'       # Dropbox App Secret
REFRESH_TOKEN = 'YOUR_REFRESH_TOKEN' # 発行済みのリフレッシュトークン

# ▼ アクセストークン再取得
response = requests.post(
    "https://api.dropboxapi.com/oauth2/token",
    data={
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    },
    auth=(APP_KEY, APP_SECRET)
)

# ▼ 結果表示
if response.status_code == 200:
    print("✅ refresh_token は有効です！")
    print("取得した access_token:", response.json().get("access_token"))
else:
    print("❌ 無効な refresh_token です。")
    print("エラー内容:", response.json())
