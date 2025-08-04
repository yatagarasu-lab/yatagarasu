import os
import openai
import dropbox
import hashlib
from utils.line_notify import push_message_to_user

# 環境変数から取得
DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LINE_USER_ID = os.getenv("LINE_USER_ID")

# 初期化
dbx = dropbox.Dropbox(DROPBOX_TOKEN)
openai.api_key = OPENAI_API_KEY

# ファイルのハッシュを計算して重複検出に使用
def file_hash(content):
    return hashlib.sha256(content).hexdigest()

# Dropbox内のすべてのファイルリストを取得
def list_files(folder_path):
    res = dbx.files_list_folder(folder_path)
    files = res.entries
    while res.has_more:
        res = dbx.files_list_folder_continue(res.cursor)
        files.extend(res.entries)
    return [f for f in files if isinstance(f, dropbox.files.FileMetadata)]

# ファイルをダウンロード（バイナリ）
def download_file(path):
    metadata, res = dbx.files_download(path)
    return res.content

# GPTで要約を生成
def summarize_text(content):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=[
                {"role": "system", "content": "以下のファイルの内容を短く要約してください。"},
                {"role": "user", "content": content.decode("utf-8", errors="ignore")[:3000]}
            ],
            temperature=0.5,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[要約失敗] {str(e)}"

# 要約＋重複チェック＋LINE通知
def summarize_file_and_notify(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)
    seen_hashes = {}

    for f in files:
        path = f.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        # 重複チェック
        if hash_value in seen_hashes:
            print(f"✅ 重複検出: {path}（同一: {seen_hashes[hash_value]}）")
            continue

        seen_hashes[hash_value] = path

        summary = summarize_text(content)

        print(f"📤 通知送信: {path}")
        push_message_to_user(
            user_id=LINE_USER_ID,
            text=f"📂 新規ファイル: {path}\n📝 要約:\n{summary}"
        )