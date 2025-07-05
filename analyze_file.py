import hashlib
import os
from dropbox_utils import list_files, download_file, delete_file, move_file
from line_push import push_line_message
from openai import OpenAI

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

hash_map = {}

def file_hash(content):
    return hashlib.sha256(content).hexdigest()

def analyze_and_clean(folder_path="/Apps/slot-data-analyzer"):
    files = list_files(folder_path)

    for file in files:
        path = file.path_display
        name = file.name
        content = download_file(path)

        # 重複チェック
        h = file_hash(content)
        if h in hash_map:
            delete_file(path)
            push_line_message(f"🗑️ 重複ファイルを削除しました: {name}")
            continue
        else:
            hash_map[h] = path

        # ChatGPTで内容を要約
        summary = ask_gpt_summary(content)

        # フォルダ振り分け（例: スロットデータ or GPT会話）
        if b"スロット" in content or b"パチンコ" in content:
            new_path = folder_path + "/スロット/" + name
        else:
            new_path = folder_path + "/GPTログ/" + name

        move_file(path, new_path)
        push_line_message(f"✅ ファイル処理完了: {name}\n概要: {summary}")


def ask_gpt_summary(content_bytes):
    try:
        content_text = content_bytes.decode("utf-8", errors="ignore")
        client = OpenAI()
        res = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "これはDropboxに送られたファイルです。中身を要約してください。"},
                {"role": "user", "content": content_text[:3000]}
            ]
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        return f"要約に失敗しました: {e}"
