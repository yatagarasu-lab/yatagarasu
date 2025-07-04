from linebot.models import TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from linebot import LineBotApi, WebhookHandler
import os

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
USER_ID = os.getenv("LINE_USER_ID")


def handle_text_event(event):
    """LINEで受信したテキストメッセージに対して返信"""
    try:
        user_message = event.message.text.strip().lower()

        # 任意のコマンドやキーワードに応じた応答
        if user_message in ["ping", "hello", "テスト"]:
            reply_text = "Botは正常に動作しています。✅"
        elif user_message == "重複削除":
            from duplicate_cleaner import find_and_remove_duplicates
            find_and_remove_duplicates()
            reply_text = "📁 Dropbox内の重複ファイルを削除しました。"
        else:
            reply_text = f"「{user_message}」を受け取りました。"

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text[:4000])
        )

    except Exception as e:
        print(f"テキスト処理エラー: {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"⚠️ エラーが発生しました: {e}")
        )
