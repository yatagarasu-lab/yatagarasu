import os
import hashlib
import dropbox
from openai import OpenAI
from PIL import Image
from io import BytesIO
import mimetypes
import base64

# 環境変数
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")

client = OpenAI(api_key=OPENAI_API_KEY)

processed_hashes = set()  # 重複判定用ハッシュ集合

def file_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()

def is_image_file(path: str) -> bool:
    mime, _ = mimetypes.guess_type(path)
    return mime and mime.startswith("image")

def analyze_file_with_gpt(filename: str, content: bytes) -> str:
    try:
        if is_image_file(filename):
            img_base64 = base64.b64encode(content).decode("utf-8")
            res = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "あなたはスロット設定判別AIです。画像やテキストから内容を要約・分析してレポートを作成してください。"},
                    {"role": "user", "content": f"以下の画像を解析してください（Base64形式）:\n{img_base64}"}
                ]
            )
        else:
            text = content.decode("utf-8", errors="ignore")
            res = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[
                    {"role": "system", "content": "あなたはスロット設定判別AIです。"},
                    {"role": "user", "content": f"以下のテキストを解析してください:\n{text}"}
                ]
            )

        return res.choices[0].message.content.strip()

    except Exception as e:
        return f"[エラー] 解析失敗: {str(e)}"

def download_and_analyze_files(dbx):
    folder_path = "/Apps/slot-data-analyzer"
    result_summary = ""

    try:
        files = dbx.files_list_folder(folder_path).entries

        for file in files:
            if isinstance(file, dropbox.files.FileMetadata):
                path = file.path_display
                _, ext = os.path.splitext(path)
                _, res = os.path.split(path)

                metadata, res = dbx.files_download(path)
                content = res.content

                h = file_hash(content)
                if h in processed_hashes:
                    continue
                processed_hashes.add(h)

                summary = analyze_file_with_gpt(path, content)
                result_summary += f"\n\n📄 **{file.name}** の解析結果:\n{summary}"

    except Exception as e:
        result_summary += f"\n[エラー発生]: {str(e)}"

    return result_summary if result_summary else None