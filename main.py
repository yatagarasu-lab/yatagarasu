from flask import Flask, request, make_response
import os
import dropbox
import requests

app = Flask(__name__)

# 環境変数から読み込み
DROPBOX_ACCESS_TOKEN = os.getenv('DROPBOX_ACCESS_TOKEN')
LINE_ACCESS_TOKEN = os.getenv('LINE_ACCESS_TOKEN')
LINE_USER_ID = os.getenv('LINE_USER_ID')

# LINE通知関数
def notify_line(message):
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{
            "type": "text",
            "text": message
        }]
    }
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)

# Webhook GET/POSTエンドポイント
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        challenge = request.args.get('challenge')
        response = make_response(challenge, 200)
        response.headers['Content-Type'] = 'text/plain'
        return response

    elif request.method == 'POST':
        print("✅ Webhook POST受信")
        try:
            dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
            result = dbx.files_list_folder(path="", limit=5)  # App Folderの場合は ""、Full Dropboxなら "/" に変更

            files = [entry.name for entry in result.entries]
            message = "📂 Dropboxに新しいファイルの変更があります：\n" + "\n".join(f"- {f}" for f in files)
            notify_line(message)

        except Exception as e:
            print("❌ Dropbox処理エラー:", str(e))
            notify_line("Dropboxのファイル取得でエラーが発生しました")

        return '', 200

# トップページ確認用
@app.route('/')
def index():
    return '✅ Dropbox Webhook サーバー稼働中'

# Renderで起動
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))