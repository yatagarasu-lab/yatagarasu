import hashlib
from io import BytesIO
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

# 重複判定用のハッシュ記録
processed_hashes = set()

def hash_file(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def analyze_and_deduplicate(dbx, entry):
    _, res = dbx.files_download(entry.path_lower)
    content = res.content
    file_hash = hash_file(content)

    if file_hash in processed_hashes:
        dbx.files_delete_v2(entry.path_lower)
        return entry.name, "Deleted (duplicate)"
    else:
        processed_hashes.add(file_hash)

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "あなたはスロットデータを解析するアシスタントです。"},
                {"role": "user", "content": content.decode(errors='ignore')}
            ]
        )

        analysis_result = response.choices[0].message["content"]
        return entry.name, analysis_result