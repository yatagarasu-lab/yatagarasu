from flask import Flask, request, jsonify
from services.dropbox_handler import handle_dropbox_webhook
from services.gpt_summarizer import summarize_and_check_duplicate
from services.line_handler import push_line_message

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def home():
    return "Yatagarasu: Dropbox × GPT × LINE Bot", 200

# DropboxのWebhookエンドポイント
@app.route("/dropbox-webhook", methods=["POST"])
def dropbox_webhook():
    # DropboxがWebhookの疎通確認のためにHEADリクエストを送る場合もある
    if request.method == "HEAD":
        return "", 200

    # Webhook POSTリクエスト処理開始
    print("📥 Dropbox Webhook 呼び出し検出")

    try:
        # ファイルの取得と要約＆重複チェック
        summaries = handle_dropbox_webhook()

        # 通知用メッセージ作成
        if not summaries:
            message = "新規ファイルはありませんでした。"
        else:
            message = "📦 Dropbox更新ファイル:\n" + "\n".join(summaries)

        # LINEに通知送信
        push_line_message(message)

        return jsonify({"status": "success"}), 200

    except Exception as e:
        print(f"[エラー] Dropbox Webhook処理失敗: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500