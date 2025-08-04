import hashlib
import openai
import os

# GPTで要約する関数（テキスト）
def summarize_text(text, max_tokens=500):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-1106-preview",
            messages=[
                {"role": "system", "content": "次のファイル内容を短く要約してください。"},
                {"role": "user", "content": text}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"要約に失敗しました: {e}"

# SHA256によるファイルの重複判定用のハッシュ生成
def file_hash(binary):
    return hashlib.sha256(binary).hexdigest()

# 重複ファイルを削除する処理（親で制御される）
def find_duplicates(files, download_func, delete_func):
    hash_map = {}
    duplicates = []

    for file in files:
        content = download_func(file.path_display)
        hash_value = file_hash(content)

        if hash_value in hash_map:
            duplicates.append(file.path_display)
            delete_func(file.path_display)
        else:
            hash_map[hash_value] = file.path_display

    return duplicates