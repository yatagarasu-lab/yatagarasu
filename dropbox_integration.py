import os
import dropbox
import openai
from requests_oauthlib import OAuth2Session

# Dropbox APIキー類
DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

# OpenAI APIキー
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


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
                print(f"\n=== {entry.name} の解析結果 ===\n{gpt_result}\n====================")
    except Exception as e:
        print(f"[Dropbox ERROR] {e}")

    return "OK", 200