import os
import json
from flask import Blueprint, request, Response
from gpt_analyzer import analyze_and_notify
from dropbox_handler import handle_dropbox_webhook

webhook_bp = Blueprint("webhook", __name__)

VERIFY_TOKEN = os.getenv("DROPBOX_VERIFY_TOKEN", "default_token")

@webhook_bp.route("/webhook", methods=["GET"])
def verify():
    challenge = request.args.get("challenge")
    return challenge, 200

@webhook_bp.route("/webhook", methods=["POST"])
def handle_webhook():
    if request.headers.get("X-Dropbox-Signature") is None:
        return "Missing signature", 400

    try:
        data = request.get_json()
        if not data:
            return "No data", 400

        # DropboxのWebhookからの通知を処理
        handle_dropbox_webhook(data)

        # GPTによる解析＆LINE通知を実行
        analyze_and_notify()

        return Response(status=200)
    except Exception as e:
        return f"Error: {str(e)}", 500
