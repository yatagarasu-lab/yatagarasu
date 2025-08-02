import os
import datetime
import dropbox
from flask import Flask, request

app = Flask(__name__)

# === GPTログ保存用関数 ===
def save_gpt_output_to_dropbox(content: str, filename_prefix="gpt_log"):
    try:
        access_token = os.getenv("DROPBOX_ACCESS_TOKEN")
        if not access_token:
            print("❌ DROPBOX_ACCESS_TOKEN が設定されていません。")
            return

        dbx = dropbox.Dropbox(access_token)
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/Apps/slot-data-analyzer/{filename_prefix}_{now}.txt"
        dbx.files_upload(content.encode('utf-8'), filename, mode=dropbox.files.WriteMode.overwrite)
        print(f"✅ GPT出力ログをDropboxに保存しました: {filename}")
    except Exception as e:
        print(f"❌ Dropbox保存エラー: {e}")

# === Webhookの受信例 ===
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if not data:
        return "No JSON received", 400

    # GPTからの出力がここにある想定（仮置き）
    gpt_reply = "これはGPTからの出力です（例）"

    # Dropboxに保存
    save_gpt_output_to_dropbox(gpt_reply)

    return "OK", 200

# === Render動作用エントリーポイント ===
if __name__ == "__main__":
    # テスト実行（Render以外のローカル検証用）
    save_gpt_output_to_dropbox("これは手動で呼び出したGPTログの保存テストです。")
    app.run(host="0.0.0.0", port=5000)