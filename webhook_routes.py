# webhook_routes.py

from flask import Blueprint, request, Response
from dropbox_utils import handle_dropbox_event

webhook_bp = Blueprint("webhook", __name__)

@webhook_bp.route("/dropbox-webhook", methods=["GET"])
def dropbox_webhook_verification():
    challenge = request.args.get("challenge")
    return Response(challenge, status=200)

@webhook_bp.route("/dropbox-webhook", methods=["POST"])
def dropbox_webhook_event():
    print("📦 Dropbox Webhook受信 ✅")
    try:
        body = request.data.decode("utf-8")
        print("📨 Webhook Body:", body)

        # イベント発生時の処理（アカウントIDなど取得可能）
        handle_dropbox_event(body)

        return Response("Webhook受信OK", status=200)
    except Exception as e:
        print("❌ Webhook処理エラー:", str(e))
        return Response("エラー", status=500)
