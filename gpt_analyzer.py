import os
from dropbox_utils import list_files, download_file, file_hash
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

processed_hashes = set()

def analyze_and_notify(line_bot_api, line_user_id):
    files = list_files()
    for file in files:
        path = file.path_display
        content = download_file(path)
        hash_value = file_hash(content)

        if hash_value in processed_hashes:
            print(f"🔁 重複スキップ: {path}")
            continue
        processed_hashes.add(hash_value)

        summary = gpt_summarize(content.decode('utf-8', errors='ignore'))
        message = f"📂 {path}\n📝 要約:\n{summary}"
        line_bot_api.push_message(line_user_id, TextSendMessage(text=message))

def gpt_summarize(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "これはDropboxにアップロードされたファイルの中身です。短く要約してください。"},
                {"role": "user", "content": text[:4000]}  # 長文防止
            ]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return f"❌ GPT解析失敗: {e}"