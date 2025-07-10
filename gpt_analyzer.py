import os
import dropbox
import hashlib
import base64
from openai import OpenAI
from dotenv import load_dotenv
from utils.dropbox_utils import get_dropbox_client_with_refresh, list_files, download_file, move_file
from utils.line_notify import send_line_push

load_dotenv()

# GPT初期化
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 分析対象フォルダ（Dropboxアプリ内の相対パス）
DROPBOX_FOLDER = "/Apps/slot-data-analyzer"

# 解析結果を保存するフォルダ
ANALYZED_FOLDER = f"{DROPBOX_FOLDER}/analyzed"
IGNORED_FOLDER = f"{DROPBOX_FOLDER}/ignored"

# 環境変数
LINE_USER_ID = os.getenv("LINE_USER_ID")


def file_hash(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()


def is_text_file(file_name: str) -> bool:
    return file_name.lower().endswith((".txt", ".log", ".csv"))


def is_image_file(file_name: str) -> bool:
    return file_name.lower().endswith((".jpg", ".jpeg", ".png"))


def analyze_with_gpt(content: str, filename: str) -> str:
    """GPTに送信して要約・解析結果を取得"""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "以下のファイル内容を要約・分析してください。"},
                {"role": "user", "content": content},
            ],
            max_tokens=2048,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[GPTエラー] {e}"


def analyze_dropbox_and_notify():
    """Dropboxをスキャンし、ファイルをGPTで解析、分類・通知"""
    dbx = get_dropbox_client_with_refresh()
    files = list_files(DROPBOX_FOLDER, dbx)

    hash_map = {}  # 重複除去用
    summary_messages = []

    for file in files:
        path = file.path_display
        name = os.path.basename(path)

        # サブフォルダはスキップ
        if "/analyzed/" in path or "/ignored/" in path:
            continue

        content = download_file(path, dbx)
        h = file_hash(content)

        if h in hash_map:
            # 重複 → 無視フォルダへ移動
            move_file(path, f"{IGNORED_FOLDER}/{name}", dbx)
            continue
        hash_map[h] = path

        # ファイルタイプ別に処理
        if is_text_file(name):
            decoded = content.decode("utf-8", errors="ignore")
            result = analyze_with_gpt(decoded, name)
            summary_messages.append(f"📄 {name}：\n{result}\n")

        elif is_image_file(name):
            result = f"🖼 {name} は画像ファイルです（OCR解析は未対応）"
            summary_messages.append(result)

        else:
            result = f"❓ {name} は未対応の形式です"
            summary_messages.append(result)

        # 処理後は analyzed フォルダへ移動
        move_file(path, f"{ANALYZED_FOLDER}/{name}", dbx)

    # LINEに送信
    full_message = "\n\n".join(summary_messages) or "📦 Dropboxに解析対象ファイルはありませんでした。"
    send_line_push(full_message)