import os
import hashlib
import dropbox
from openai import OpenAI
from services.dropbox_utils import list_files, download_file

# Dropboxアクセストークンの取得（refresh_token方式）
def get_dropbox_access_token():
    import requests
    response = requests.post(
        "https://api.dropboxapi.com/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": os.environ.get("DROPBOX_REFRESH_TOKEN"),
            "client_id": os.environ.get("DROPBOX_CLIENT_ID"),
            "client_secret": os.environ.get("DROPBOX_CLIENT_SECRET"),
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]

# ファイルのSHA-256ハッシュを計算
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# GPTで要約処理
def summarize_text_with_gpt(text):
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "以下のテキストを要約してください。"},
            {"role": "user", "content": text}
        ],
        temperature=0.3,
        max_tokens=400
    )
    return response.choices[0].message.content.strip()

# 重複ファイルを探して削除、要約も行う
def process_dropbox_files(folder_path="/"):
    access_token = get_dropbox_access_token()
    dbx = dropbox.Dropbox(access_token)
    files = list_files(folder_path, dbx)

    seen_hashes = {}
    for file in files:
        path = file.path_display
        content = download_file(path, dbx)
        hash_value = file_hash(content)

        if hash_value in seen_hashes:
            print(f"重複ファイルを削除: {path}（同一: {seen_hashes[hash_value]}）")
            dbx.files_delete_v2(path)
        else:
            seen_hashes[hash_value] = path

            # テキストならGPTで要約（拡張子などから判定）
            if path.endswith(".txt"):
                text = content.decode("utf-8", errors="ignore")
                summary = summarize_text_with_gpt(text)
                print(f"{path} の要約: {summary}")