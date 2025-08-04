import hashlib
import hmac
import os
from flask import request, Response
from yatagarasu import analyze_latest_file

DROPBOX_APP_SECRET = os.environ.get("DROPBOX_APP_SECRET")  # Render環境変数で設定

def verify_signature(request):
    signature = request.headers.get("X-Dropbox-Signature", "")
    if not signature or not DROPBOX_APP_SECRET:
        return False
    computed_sig = hmac.new(
        key=DROPBOX_APP_SECRET.encode(),
        msg=request.data,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, computed_sig)

def handle_dropbox_webhook(request):
    # webhook検証（GETリクエスト）
    if request.method == 'GET':
        challenge = request.args.get("challenge")
        return Response(challenge, status=200)

    # webhook通知（POSTリクエスト）
    if request.method == 'POST':
        if not verify_signature(request):
            return Response("Invalid signature", status=403)
        
        print("✅ Dropbox Webhook 受信 → GPT解析を開始")
        analyze_latest_file()  # ファイル更新時に解析実行
        return Response("OK", status=200)

    return Response("Invalid request", status=400)