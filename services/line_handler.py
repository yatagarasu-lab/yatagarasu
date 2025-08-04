from flask import request, abort
from linebot.v3.webhook import WebhookParser
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient, ReplyMessageRequest, TextMessage
import os

# 環境変数からLINE設定取得
channel_secret = os.environ.get("LINE_CHANNEL_SECRET")
channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")

# バリデーション
if not channel_secret or not channel_access_token:
    raise ValueError("LINEの環境変数が設定されていません。")

parser = WebhookParser(channel_secret)
configuration = Configuration(access_token=channel_access_token)

def handle_line_webhook():
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data(as_text=True)

    try:
        events = parser.parse(body, signature)
    except Exception as e:
        print(f"❌ LINEイベントのパース失敗: {e}")
        abort(400)

    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
            user_text = event.message.text
            user_id = event.source.user_id

            # ここでGPTなどを使った応答処理を行う（今回は固定返信）
            reply_text = "ありがとうございます"

            with ApiClient(configuration) as api_client:
                line_bot_api = MessagingApi(api_client)
                line_bot_api.reply_message(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text=reply_text)]
                    )
                )

    return "✅ LINEイベント処理完了"