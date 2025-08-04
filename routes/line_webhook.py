import os
import json
from flask import Blueprint, request, abort
from openai import OpenAI
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage
)

# Flask Blueprint
line_webhook_bp = Blueprint("line_webhook", __name__)

# 環境変数から設定
channel_secret = os.environ.get("LINE_CHANNEL_SECRET")
channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
openai_api_key = os.environ.get("OPENAI_API_KEY")

if not channel_secret or not channel_access_token:
    raise ValueError("LINEの設定が正しくありません。")

handler = WebhookHandler(channel_secret)
configuration = Configuration(access_token=channel_access_token)

@line_webhook_bp.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Line-Signature")
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except Exception as e:
        abort(400, f"Signature Error: {str(e)}")

    return "OK"

# メッセージイベントの処理
@handler.add(event=WebhookHandler.MessageEvent)
def handle_message(event):
    if event.message.type != "text":
        return

    user_message = event.message.text.strip()

    # OpenAI GPTによる返信生成
    client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "あなたはLINE BOTです。短く丁寧に応答してください。"},
            {"role": "user", "content": user_message}
        ]
    )

    reply_text = response.choices[0].message.content.strip()

    # LINEへ返信送信
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
