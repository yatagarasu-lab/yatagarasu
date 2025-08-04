import os
import dropbox
import openai
import requests
from requests_oauthlib import OAuth2Session

# Dropbox
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# LINE
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID = os.getenv("LINE_USER_ID")


def get_dropbox_access_token():
    token_url = "https://api.dropbox.com/oauth2/token"
    session = OAuth2Session(client_id=DROPBOX_APP_KEY)
    token = session.refresh_token(
        token_url=token_url,
        refresh_token=DROPBOX_REFRESH_TOKEN,
        client_id=DROPBOX_APP_KEY,
        client_secret=DROPBOX_APP_SECRET
    )
    return token["access_token"]


def analyze_file_with_gpt(file_content: str) -> str:
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "あなたはDropboxに保存されたテキストファイルを分析するAIです。"},
                {"role": "user", "content": file_content}
            ],
            max_tokens=500
        )
        return response.choices[0].message["content"]
    except Exception as e:
        return f"[GPT ERROR] {e}"


def send_line_message(text: str):
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    data = {
        "to": LINE_USER_ID,
        "messages": [{"type": "text", "text": text}]
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        print(f"[LINE] Status: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[LINE ERROR] {e}")


def handle_dropbox_webhook():
    access_token = get_dropbox_access_token()
    dbx = dropbox.Dropbox(access_token)

    try:
        result = dbx.files_list_folder(path="/Apps/slot-data-analyzer")
        for entry in result.entries:
            if isinstance(entry, dropbox.files.FileMetadata):
                _, res = dbx.files_download(entry.path_display)
                content = res.content.decode("utf-8")

                gpt_result = analyze_file_with_gpt(content)

                message = f"✅ {entry.name} の解析結果：\n{gpt_result}"
                print(message)
                send_line_message(message)
    except Exception as e:
        print(f"[Dropbox ERROR] {e}")
        send_line_message(f"[Dropbox ERROR] {e}")

    return "OK", 200