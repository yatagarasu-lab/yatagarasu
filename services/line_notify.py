import os
from linebot.v3.messaging import Configuration, MessagingApi, ApiClient, PushMessageRequest, TextMessage

# 環境変数からLINEアクセストークンとユーザーIDを取得
channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
user_id = os.environ.get("LINE_USER_ID")  # 固定ユーザーにPush

if not channel_access_token or not user_id:
    raise ValueError("LINEのアクセストークンまたはユーザーIDが設定されていません。")

configuration = Configuration(access_token=channel_access_token)

def send_line_message(message: str):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=message)]
            )
        )
