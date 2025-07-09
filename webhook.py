from flask import Blueprint, request, abort
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from log_utils import delete_old_logs  # ログ削除関数のインポート

webhook_bp = Blueprint("webhook", __name__)
handler = WebhookHandler("YOUR_CHANNEL_SECRET")

@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    # リクエストの検証
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    # ログ削除をここでも実行（main.pyと重複しても問題なし）
    delete_old_logs()

    return "OK"