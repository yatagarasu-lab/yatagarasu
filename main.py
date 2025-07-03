from flask import Flask, request
import dropbox
import requests

app = Flask(__name__)

# ★あなたのアクセストークンに差し替えてください
DROPBOX_ACCESS_TOKEN =sl.u.AF3mWN0y-iXTJFh2iirrpTyqWovw_4s5K_rPjGu4XhX4-wS94j8QSuVW97U5AHPmE4vHv7jcYtFPCcTfrC11pNsKuvkC7Gls54HvDQ9n-81mEOz6DGiAYVbNGl7xduXoK..."

# ★あなたのLINEのチャネルアクセストークンに差し替えてください
LINE_CHANNEL_ACCESS_TOKEN =sxrPtKafZjwhLlzHKZiehdnYQZUnj0oEzYC/JxpQOzsfA8DM6UvoM47mual7Br/SnTWU7G+2NUU+2DTsk2EW1duvF9OBFiNravuROk8FH0qQ/AUwIwi1sW6/4A2OzOncXDG3YJr1k5KKFzn5J5TXvQdB04t89/1O/w1cDnyilFU=

# LINE通知送信関数
def send_line_message(message):
    headers = {
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "to": "あなたのユーザーID or グループID",
        "messages": [{"type": "text", "text": message}]
    }
    requests.post("https://api.line.me/v2/bot/message/push", headers=headers, json=data)

# Dropboxからファイル名一覧を取得してLINE通知
def notify_dropbox_files():
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    result = dbx.files_list_folder(path="/スロットデータ")  # 任意のフォルダ名に変更OK
    file_names = [entry.name for entry in result.entries]
    if file_names:
        message = "Dropboxに新しいファイルがあります:\n" + "\n".join(file_names)
    else:
        message = "Dropboxにファイルが見つかりません。"
    send_line_message(message)

# Webhook受信時に通知を実行
@app.route("/callback", methods=["POST"])
def callback():
    notify_dropbox_files()
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "動作中", 200

if __name__ == "__main__":
    app.run()