import hashlib
import hmac
import os
from flask import Response
from yatagarasu import analyze_latest_file

DROPBOX_SECRET = os.environ.get("DROPBOX_APP_SECRET")

def verify_signature(request):
    """Dropboxからの署名が正しいか検証"""
    signature = request.headers.get("X-Dropbox-Signature")
    if not signature or not DROPBOX_SECRET:
        return False
    computed_signature = hmac.new(
        DROPBOX_SECRET.encode(),
        msg=request.data,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, computed_signature)

def handle_dropbox_webhook(request):
    """DropboxからのWebhook POSTに対応する"""
    # URL認証用のGETリクエスト（Webhook登録時など）
    if request.method == 'GET':
        challenge = request.args.get("challenge")
        return Response(challenge, status=200)

    # POSTリクエスト：ファイルが追加された通知
    if request.method == 'POST':
        if not verify_signature(request):
            return Response("Invalid signature", status=403)

        # 通知内容をログに残す（必要なら）
        print("✅ DropboxからのWebhook受信: ファイル更新を検知しました")

        # 最新ファイルを解析
        result = analyze_latest_file()

        # 成功レスポンス
        return Response(f"解析完了: {result}", status=200)

    return Response("Invalid method", status=405)