from flask import Flask, request
import dropbox
import os

app = Flask(__name__)

# 環境変数からDropbox認証情報を取得
DROPBOX_REFRESH_TOKEN = os.environ.get("DROPBOX_REFRESH_TOKEN")
DROPBOX_APP_KEY = os.environ.get("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")

# Dropboxインスタンス作成（リフレッシュトークン方式）
dbx = dropbox.Dropbox(
    oauth2_refresh_token=DROPBOX_REFRESH_TOKEN,
    app_key=DROPBOX_APP_KEY,
    app_secret=DROPBOX_APP_SECRET
)

@app.route('/')
def index():
    return 'Dropbox webhook active'

@app.route('/webhook', methods=['POST'])
def webhook():
    print("Webhook triggered")
    # ここにファイル処理のロジックを追加する
    return '', 200

if __name__ == '__main__':
    app.run(debug=True)