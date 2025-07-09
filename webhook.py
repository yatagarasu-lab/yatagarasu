from flask import Blueprint, request
import os
from analyze_file import analyze_and_notify
import hmac
import hashlib
import datetime
import pytz

webhook_bp = Blueprint("dropbox_webhook", __name__)

DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")

# 夜間判定（22:00～翌6:00 のみ実行許可）
def is_nighttime():
    tz = pytz.timezone("Asia/Tokyo")
    now = datetime.datetime.now(tz).time()
    return now >= datetime.time(22, 0) or now <= datetime.time(6, 0)

# Dropbox webhookの検証用（GET）
@webhook_bp.route("/webhook", methods=["GET"])
def verify():
    challenge = request.args.get("challenge")
    return challenge, 200

# Dropbox webhookイベント受信（POST）
@webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    # セキュリティチェック（署名の検証）
    signature = request.headers.get("X-Dropbox-Signature")
    expected = hmac.new(
        key=DROPBOX_APP_SECRET.encode(),
        msg=request.data,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return "Invalid signature", 403

    if not is_nighttime():
        return "昼間のため解析をスキップ", 200

    # メイン処理：Dropbox内の新ファイルを解析＆通知
    try:
        analyze_and_notify()
        return "解析＆通知 実行", 200
    except Exception as e:
        return f"Error during processing: {str(e)}", 500