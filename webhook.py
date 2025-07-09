from flask import Blueprint, request, Response
from analyze_file import analyze_dropbox_files
from datetime import datetime
import pytz

webhook_bp = Blueprint("webhook", __name__)

# 日本時間に変換
def is_night_time_japan():
    jst = pytz.timezone("Asia/Tokyo")
    now = datetime.now(jst)
    return now.hour >= 22 or now.hour < 6  # 夜22時～翌6時

@webhook_bp.route("/webhook", methods=["GET"])
def webhook_verify():
    challenge = request.args.get("challenge")
    return Response(challenge, status=200)

@webhook_bp.route("/webhook", methods=["POST"])
def webhook_event():
    if is_night_time_japan():
        analyze_dropbox_files()
    else:
        print("[⏸] 日中時間帯のため解析スキップ（22:00〜6:00のみ処理）")
    return Response(status=200)
