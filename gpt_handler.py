import os
import hashlib
import dropbox
from dropbox.files import FileMetadata
from line_handler import push_line_message
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

# OpenAI APIクライアント初期化
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Dropbox OAuth2.0 (リフレッシュトークン方式)
dbx = dropbox.Dropbox(
    oauth2_refresh_token=os.getenv("DROPBOX_REFRESH_TOKEN"),
    app_key=os.getenv("DROPBOX_APP_KEY"),
    app_secret=os.getenv("DROPBOX_APP_SECRET")
)

# 重複チェックに使うハッシュ辞書（セッション中）
hash_map = {}

def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def summarize_text(text: str) -> str:
    try:
        system_prompt = "これはユーザーから送られたパチスロや設定予想に関するデータです。内容を要約してください。"
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"要約失敗: {e}"

def process_dropbox_folder(folder_path="/Apps/slot-data-analyzer"):
    try:
        files = dbx.files_list_folder(folder_path).entries
        for file in files:
            if isinstance(file, FileMetadata):
                path = file.path_display
                metadata, res = dbx.files_download(path)
                content = res.content
                hash_value = file_hash(content)

                if hash_value in hash_map:
                    dbx.files_delete_v2(path)
                    print(f"🗑️ 重複削除: {path}")
                    continue

                hash_map[hash_value] = path

                if file.name.lower().endswith(".txt"):
                    text = content.decode("utf-8")
                    summary = summarize_text(text)
                    push_line_message(f"[要約]\n{summary}")
                else:
                    push_line_message(f"新規ファイル検出: {file.name}")
    except Exception as e:
        push_line_message(f"[エラー] Dropbox処理に失敗: {e}")