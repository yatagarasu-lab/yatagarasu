import os
import hashlib
import dropbox
import openai

dbx = dropbox.Dropbox(os.environ["DROPBOX_ACCESS_TOKEN"])
openai.api_key = os.environ["OPENAI_API_KEY"]

def file_hash(content):
    return hashlib.md5(content).hexdigest()

def analyze_and_store(content, filename, folder, is_image=False):
    print(f"解析開始: {filename}")

    # 重複判定
    hash_val = file_hash(content)
    try:
        existing_files = dbx.files_list_folder(folder).entries
        for f in existing_files:
            if isinstance(f, dropbox.files.FileMetadata):
                meta, res = dbx.files_download(f.path_display)
                if file_hash(res.content) == hash_val:
                    print(f"重複ファイル: {f.name} → スキップ")
                    return
    except dropbox.exceptions.ApiError:
        dbx.files_create_folder_v2(folder)

    # GPT解析
    if is_image:
        result = f"画像 {filename} を受信しました（解析準備中）"
    else:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたは優秀な要約者です。"},
                {"role": "user", "content": content}
            ]
        )
        result = response.choices[0].message.content

    summary_path = f"{folder}/解析_{filename}.txt"
    dbx.files_upload(result.encode(), summary_path)
    print(f"保存完了: {summary_path}")